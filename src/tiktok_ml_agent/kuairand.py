"""Safe KuaiRand-Pure access using the organizer evaluator.

Unlike the starter loader, this adapter intentionally never reads the hidden-test
label column. Test rows are returned only as identifier/feature records for
submission generation.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterator, Literal

from .benchmark import BenchmarkAdapter
from .contracts import BenchmarkSpec, TestAccessError, hash_file


SplitName = Literal["train", "valid", "test"]
SPLIT_DATES: dict[SplitName, tuple[int, int]] = {
    "train": (20220408, 20220421),
    "valid": (20220422, 20220428),
    "test": (20220429, 20220508),
}


@dataclass(frozen=True, slots=True)
class KuaiRandRow:
    date: int
    user_id: str
    video_id: str
    author_id: str
    tab: str
    duration_ms: float
    label: int | None


def starter_kuairand_pure_spec(starter_kit_dir: str | Path) -> BenchmarkSpec:
    starter_kit_dir = Path(starter_kit_dir)
    evaluator = starter_kit_dir / "evaluate.py"
    return BenchmarkSpec(
        benchmark_id="kuairand-pure",
        profile_id="starter-long-view-gauc-ndcg5-v1",
        label="long_view",
        metrics=("GAUC", "nDCG@5", "primary"),
        evaluator_path=str(evaluator),
        evaluator_sha256=hash_file(evaluator),
        epsilon=0.002,
        patience=3,
        source_note=(
            "Interpretation - not explicit organizer wording: provisional runnable starter profile "
            "while PDF label/metric ambiguity is unresolved."
        ),
    )


class KuaiRandPureData:
    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)

    def _authors(self) -> dict[str, str]:
        path = self.data_dir / "video_features_basic_pure.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            return {row["video_id"]: row["author_id"] for row in csv.DictReader(handle)}

    def _log_paths(self) -> tuple[Path, Path]:
        return (
            self.data_dir / "log_standard_4_08_to_4_21_pure.csv",
            self.data_dir / "log_standard_4_22_to_5_08_pure.csv",
        )

    def rows(self, split: SplitName, include_labels: bool = True) -> list[KuaiRandRow]:
        if split == "test" and include_labels:
            raise TestAccessError("KuaiRand test labels are prohibited in candidate-facing data access")
        if split not in SPLIT_DATES:
            raise ValueError(f"unknown split: {split}")
        lower, upper = SPLIT_DATES[split]
        authors = self._authors()
        output: list[KuaiRandRow] = []
        for path in self._log_paths():
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                header = next(reader)
                positions = {name: index for index, name in enumerate(header)}
                required = {"date", "user_id", "video_id", "tab", "duration_ms"}
                missing = required - positions.keys()
                if missing:
                    raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
                if include_labels and "long_view" not in positions:
                    raise ValueError(f"{path} is missing the development label column")
                for values in reader:
                    # Select only fields that candidate-facing code is entitled to use. In
                    # particular, test rows never create a Python value for `long_view`.
                    date = int(values[positions["date"]])
                    if not lower <= date <= upper:
                        continue
                    video_id = values[positions["video_id"]]
                    label = int(values[positions["long_view"]] != "0") if include_labels else None
                    output.append(
                        KuaiRandRow(
                            date=date,
                            user_id=values[positions["user_id"]],
                            video_id=video_id,
                            author_id=authors.get(video_id, "UNK"),
                            tab=values[positions["tab"]],
                            duration_ms=float(values[positions["duration_ms"]]),
                            label=label,
                        )
                    )
        return output

    def data_fingerprint(self) -> str:
        """Fingerprint permitted rows without hashing or returning hidden-test labels."""
        digest = sha256()
        for split in ("train", "valid"):
            for row in self.rows(split, include_labels=True):
                digest.update(repr(row).encode())
        for row in self.rows("test", include_labels=False):
            digest.update(
                repr((row.date, row.user_id, row.video_id, row.author_id, row.tab, row.duration_ms)).encode()
            )
        return digest.hexdigest()


class KuaiRandPureAdapter:
    def __init__(self, starter_kit_dir: str | Path, data_dir: str | Path) -> None:
        self.spec = starter_kuairand_pure_spec(starter_kit_dir)
        self.data = KuaiRandPureData(data_dir)
        self.evaluator = BenchmarkAdapter.from_organizer_file(self.spec)

    def development_rows(self, split: Literal["train", "valid"]) -> list[KuaiRandRow]:
        self.spec.assert_development_split(split)
        return self.data.rows(split, include_labels=True)

    def submission_rows(self) -> list[KuaiRandRow]:
        return self.data.rows("test", include_labels=False)

    def score_validation(self, rows: list[KuaiRandRow], scores: list[float]) -> dict[str, float]:
        if any(row.label is None for row in rows):
            raise TestAccessError("validation scoring requires permitted labeled validation rows")
        return self.evaluator.score_development(
            "valid",
            [row.user_id for row in rows],
            [int(row.label) for row in rows if row.label is not None],
            scores,
        )

"""Streaming preflight adapters for official KuaiRand-1K/27K bonus artifacts."""

from __future__ import annotations

import csv
import glob
import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterator, Literal

from .contracts import TestAccessError


Split = Literal["train", "valid", "test"]
DATES: dict[Split, tuple[int, int]] = {"train": (20220408, 20220421), "valid": (20220422, 20220428), "test": (20220429, 20220508)}
REQUIRED_COLUMNS = {"user_id", "video_id", "date", "time_ms", "long_view", "duration_ms", "tab"}


@dataclass(frozen=True, slots=True)
class ScaleArtifactAdapter:
    variant: Literal["1k", "27k"]
    data_dir: Path

    def _log_files(self) -> list[Path]:
        suffix = self.variant
        files = sorted(Path(path) for path in glob.glob(str(self.data_dir / f"log_standard_*_{suffix}*.csv")))
        if not files:
            raise FileNotFoundError(f"no standard log files found for KuaiRand-{self.variant.upper()}")
        return files

    def _files_for_split(self, split: Split) -> list[Path]:
        """Use the official date-named partitions when available.

        Falling back to every log keeps the adapter usable if an organizer
        changes filenames, while the normal route avoids re-reading the 27K
        train log during validation and vice versa.
        """
        token = "4_08_to_4_21" if split == "train" else "4_22_to_5_08"
        selected = [path for path in self._log_files() if token in path.name]
        return selected or self._log_files()

    @staticmethod
    def _positions(path: Path, header: list[str]) -> dict[str, int]:
        positions = {name: index for index, name in enumerate(header)}
        missing = REQUIRED_COLUMNS - positions.keys()
        if missing:
            raise ValueError(f"{path} missing required columns: {sorted(missing)}")
        return positions

    def iter_rows(self, split: Split, *, include_labels: bool = False) -> Iterator[dict[str, str | None]]:
        if split == "test" and include_labels:
            raise TestAccessError("bonus test labels are prohibited during development")
        lo, hi = DATES[split]
        for path in self._files_for_split(split):
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                header = next(reader)
                positions = self._positions(path, header)
                for values in reader:
                    date = int(values[positions["date"]])
                    if not lo <= date <= hi:
                        continue
                    row = {name: values[positions[name]] for name in ("user_id", "video_id", "date", "time_ms", "duration_ms", "tab")}
                    row["long_view"] = values[positions["long_view"]] if include_labels else None
                    yield row

    def preflight(self) -> dict[str, object]:
        """Count and fingerprint all dated splits in one feature-safe pass."""
        counts: dict[str, int] = {}
        digest = sha256()
        split_for_date: dict[int, Split] = {}
        for split, (lo, hi) in DATES.items():
            split_for_date.update({date: split for date in range(lo, hi + 1)})
        counts = {split: 0 for split in DATES}
        for path in self._log_files():
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                positions = self._positions(path, next(reader))
                for values in reader:
                    split = split_for_date.get(int(values[positions["date"]]))
                    if split is None:
                        continue
                    row = {name: values[positions[name]] for name in ("user_id", "video_id", "date", "time_ms", "duration_ms", "tab")}
                    # Test long_view is intentionally not indexed or materialized.
                    row["long_view"] = values[positions["long_view"]] if split != "test" else None
                    counts[split] += 1
                    digest.update(repr(tuple(row.items())).encode())
        return {"variant": self.variant, "data_dir": str(self.data_dir), "log_files": [str(path) for path in self._log_files()], "split_counts": counts, "feature_only_test_fingerprint": digest.hexdigest()}


def write_preflight(adapter: ScaleArtifactAdapter, path: str | Path) -> Path:
    payload = adapter.preflight()
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path

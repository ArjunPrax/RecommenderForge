"""Bounded-memory item-popularity baselines for KuaiRand bonus artifacts.

The exact dictionary model is useful for 1K.  It is deliberately not used by
default on 27K: a Python dictionary of the full 27K item universe is an
unbounded laptop-memory commitment.  The 27K route uses a fixed-size, stable
hash table and evaluates validation in user-consistent shards.

Both long 27K passes -- sharded validation and feature-only output generation
-- are resumable.  Progress is published atomically beside the artifact and is
only honoured when the frozen model, data, evaluator, configuration, and output
target all still match, so a resumed run cannot silently blend two identities.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping, Protocol
import csv
import io
import json
import math
import os
import shutil
import tempfile
import zlib

import numpy as np

from .benchmark import BenchmarkAdapter
from .contracts import BenchmarkSpec, hash_file, utc_now
from .scale import ScaleArtifactAdapter

RESUME_SCHEMA = "kuairand-scale-resume-v1"
SUBMISSION_HEADER = ("row_id", "user_id", "video_id", "score")


class ScaleResumeMismatch(ValueError):
    """Raised when persisted progress does not describe the current run."""


@dataclass(frozen=True, slots=True)
class ScaleProgress:
    """Checkpoint boundary handed to an optional progress hook."""

    operation: str
    stage: str
    rows_completed: int
    shards_completed: int = 0


@dataclass(frozen=True, slots=True)
class StreamingPopularity:
    positives: dict[str, int]
    totals: dict[str, int]
    global_rate: float

    def score(self, video_id: str, tab: str | None = None) -> float:
        total = self.totals.get(video_id, 0)
        # Smoothed rate is stable for one-off videos.
        return (self.positives.get(video_id, 0) + 5 * self.global_rate) / (total + 5)


class PopularityScorer(Protocol):
    global_rate: float

    def score(self, video_id: str, tab: str | None = None) -> float: ...


@dataclass(frozen=True, slots=True)
class HashedStreamingPopularity:
    """Fixed-memory popularity table using a cross-run-stable item hash."""

    positives: np.ndarray
    totals: np.ndarray
    global_rate: float
    bits: int

    def _bucket(self, video_id: str) -> int:
        return zlib.crc32(video_id.encode("utf-8")) & ((1 << self.bits) - 1)

    def score(self, video_id: str, tab: str | None = None) -> float:
        bucket = self._bucket(video_id)
        return (float(self.positives[bucket]) + 5 * self.global_rate) / (float(self.totals[bucket]) + 5)


@dataclass(frozen=True, slots=True)
class TabConditionedHashedPopularity:
    """Bounded item and item×tab rate tables for an inference-known context cross."""

    item_positives: np.ndarray
    item_totals: np.ndarray
    item_tab_positives: np.ndarray
    item_tab_totals: np.ndarray
    global_rate: float
    bits: int
    item_weight: float

    def _bucket(self, token: str) -> int:
        return zlib.crc32(token.encode("utf-8")) & ((1 << self.bits) - 1)

    def _rate(self, positives: np.ndarray, totals: np.ndarray, token: str) -> float:
        bucket = self._bucket(token)
        return (float(positives[bucket]) + 5 * self.global_rate) / (float(totals[bucket]) + 5)

    def score(self, video_id: str, tab: str | None = None) -> float:
        item_rate = self._rate(self.item_positives, self.item_totals, video_id)
        tab_rate = self._rate(self.item_tab_positives, self.item_tab_totals, f"{video_id}\x1f{tab or 'UNK'}")
        return self.item_weight * item_rate + (1 - self.item_weight) * tab_rate


def save_scale_model(model: PopularityScorer, path: str | Path) -> Path:
    """Persist a fitted bounded model so a submission never retrains it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(model, HashedStreamingPopularity):
        np.savez(path, model_type="hashed_item", positives=model.positives, totals=model.totals, global_rate=model.global_rate, bits=model.bits)
    elif isinstance(model, TabConditionedHashedPopularity):
        np.savez(path, model_type="hashed_item_tab", item_positives=model.item_positives, item_totals=model.item_totals, item_tab_positives=model.item_tab_positives, item_tab_totals=model.item_tab_totals, global_rate=model.global_rate, bits=model.bits, item_weight=model.item_weight)
    else:
        raise ValueError("only bounded hashed scale models can be checkpointed for scalable submission")
    return path


def load_scale_model(path: str | Path) -> PopularityScorer:
    """Load a bounded scale checkpoint without touching any data labels."""
    with np.load(Path(path), allow_pickle=False) as archive:
        model_type = str(archive["model_type"].item())
        if model_type == "hashed_item":
            return HashedStreamingPopularity(archive["positives"], archive["totals"], float(archive["global_rate"]), int(archive["bits"]))
        if model_type == "hashed_item_tab":
            return TabConditionedHashedPopularity(archive["item_positives"], archive["item_totals"], archive["item_tab_positives"], archive["item_tab_totals"], float(archive["global_rate"]), int(archive["bits"]), float(archive["item_weight"]))
    raise ValueError("unrecognized scale model checkpoint")


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _source_signature(adapter: ScaleArtifactAdapter, split: str) -> str:
    """Cheap structural identity of the exact log files this split will read.

    Re-using the adapter's own resolution keeps this from drifting into a
    second, divergent glob.  Name/size/mtime is deliberately *not* a content
    hash: a full 27K content pass costs more than the run it would protect, so
    the strong identity stays the caller-supplied `data_fingerprint` from the
    recorded preflight and this only catches a replaced or truncated source.
    """
    entries = [
        {"name": path.name, "bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns}
        # Private access is deliberate: the adapter owns which files a split reads.
        for path in sorted(adapter._files_for_split(split))  # noqa: SLF001
    ]
    return _canonical_sha256({"files": entries})


def _run_identity(
    *,
    operation: str,
    adapter: ScaleArtifactAdapter,
    split: str,
    model_path: Path,
    target: Path,
    configuration: Mapping[str, Any],
    data_fingerprint: str | None,
    evaluator_path: str | Path | None,
) -> dict[str, str | None]:
    """Every field a resumed run must still agree with before reusing progress."""
    return {
        "schema": RESUME_SCHEMA,
        "operation": operation,
        "variant": adapter.variant,
        "split": split,
        "model_sha256": hash_file(model_path),
        "data_fingerprint": data_fingerprint,
        "evaluator_sha256": hash_file(evaluator_path) if evaluator_path is not None else None,
        "configuration_sha256": _canonical_sha256(dict(configuration)),
        "source_signature": _source_signature(adapter, split),
        "target": str(target.resolve()),
    }


def _write_state(path: Path, payload: Mapping[str, Any]) -> None:
    """Publish progress atomically so a crash never leaves a torn state file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial")
    partial.write_text(json.dumps(dict(payload) | {"updated_at": utc_now()}, indent=2, sort_keys=True), encoding="utf-8")
    partial.replace(path)


def _load_state(path: Path, identity: Mapping[str, str | None]) -> dict[str, Any] | None:
    """Return stored progress, or refuse it when any identity field differs."""
    if not path.is_file():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ScaleResumeMismatch(f"resume state at {path} is unreadable") from error
    stored = state.get("identity")
    if not isinstance(stored, dict):
        raise ScaleResumeMismatch(f"resume state at {path} carries no run identity")
    differing = sorted(key for key in set(stored) | set(identity) if stored.get(key) != identity.get(key))
    if differing:
        raise ScaleResumeMismatch(
            f"resume state at {path} does not match this run; differing fields: {', '.join(differing)}"
        )
    return state


def _truncate_to(path: Path, length: int) -> None:
    """Drop any bytes written after the last recorded checkpoint boundary."""
    size = path.stat().st_size
    if size < length:
        raise ScaleResumeMismatch(f"{path} is shorter than its recorded checkpoint; progress is stale")
    if size > length:
        with path.open("r+b") as handle:
            handle.truncate(length)


def _stream_digest(path: Path) -> Any:
    """Digest an existing prefix without holding it in memory.

    The 27K output is ~114.8M rows, so a resume must never read the partial
    artifact back as one bytes object.
    """
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest


class _HashedCsvWriter:
    """Write starter-schema rows while tracking exact bytes and a digest.

    The digest is maintained incrementally so a checkpoint costs nothing, and
    byte counts come from the encoded text rather than `TextIOWrapper.tell`,
    whose offset is documented as opaque.
    """

    def __init__(self, handle: io.TextIOBase, *, digest: Any = None, bytes_written: int = 0) -> None:
        self._handle = handle
        self._buffer = io.StringIO()
        self._writer = csv.writer(self._buffer)
        self._digest = digest if digest is not None else sha256()
        self.bytes_written = bytes_written

    def writerow(self, row: tuple[Any, ...]) -> None:
        self._buffer.seek(0)
        self._buffer.truncate(0)
        self._writer.writerow(row)
        text = self._buffer.getvalue()
        self._handle.write(text)
        encoded = text.encode("utf-8")
        self._digest.update(encoded)
        self.bytes_written += len(encoded)

    def sync(self) -> None:
        self._handle.flush()
        os.fsync(self._handle.fileno())

    @property
    def content_sha256(self) -> str:
        return self._digest.hexdigest()


def generate_scale_submission(
    *, model_path: str | Path, variant: str, data_dir: str | Path, output_path: str | Path,
) -> dict[str, float | str]:
    """Stream a feature-only starter-schema output from a frozen scale model."""
    result = generate_scale_submission_resumable(
        model_path=model_path, variant=variant, data_dir=data_dir, output_path=output_path, state_path=None,
    )
    return {key: result[key] for key in ("output", "rows", "model_sha256")}


def generate_scale_submission_resumable(
    *,
    model_path: str | Path,
    variant: str,
    data_dir: str | Path,
    output_path: str | Path,
    state_path: str | Path | None,
    data_fingerprint: str | None = None,
    evaluator_path: str | Path | None = None,
    checkpoint_every: int = 100_000,
    progress_hook: Callable[[ScaleProgress], None] | None = None,
    resume: bool = True,
) -> dict[str, float | str]:
    """Generate a feature-only output that can survive an interrupted 27K pass.

    Rows are appended to a sibling `.partial` file and the final path is only
    replaced once every row is written, so the atomic publication guarantee is
    unchanged.  When `state_path` is given, progress is checkpointed every
    `checkpoint_every` rows and a later call resumes from that boundary --
    but only if the frozen model, data, evaluator, configuration, and output
    target are all still identical.
    """
    if checkpoint_every < 1:
        raise ValueError("checkpoint_every must be at least one row")
    model_path = Path(model_path)
    model = load_scale_model(model_path)
    adapter = ScaleArtifactAdapter(variant, Path(data_dir))
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = output_path.with_name(f"{output_path.name}.partial")
    state_file = Path(state_path) if state_path is not None else None

    identity = _run_identity(
        operation="output",
        adapter=adapter,
        split="test",
        model_path=model_path,
        target=output_path,
        configuration={"operation": "output", "header": list(SUBMISSION_HEADER)},
        data_fingerprint=data_fingerprint,
        evaluator_path=evaluator_path,
    )

    start_row = 0
    state = _load_state(state_file, identity) if state_file is not None and resume else None
    if state is not None and state.get("stage") == "complete":
        # A finished, identity-matching run is reproducible; do not rewrite it.
        return {
            "output": str(output_path), "rows": float(state["rows_completed"]),
            "model_sha256": identity["model_sha256"], "output_sha256": str(state["content_sha256"]),
            "resumed_from_row": float(state["rows_completed"]), "resumed_stage": "complete",
        }
    resume_digest = None
    if state is not None and partial_path.is_file():
        _truncate_to(partial_path, int(state["bytes_written"]))
        # One streaming pass both verifies the prefix and seeds the running digest.
        resume_digest = _stream_digest(partial_path)
        if resume_digest.hexdigest() != state["content_sha256"]:
            raise ScaleResumeMismatch("partial output does not match its recorded checkpoint digest")
        start_row = int(state["rows_completed"])
    resumed_from = start_row

    checkpoints = 0
    rows = start_row
    with partial_path.open("a" if start_row else "w", newline="", encoding="utf-8") as handle:
        writer = _HashedCsvWriter(
            handle,
            digest=resume_digest,
            bytes_written=partial_path.stat().st_size if start_row else 0,
        )
        if not start_row:
            writer.writerow(SUBMISSION_HEADER)
        for row_id, row in enumerate(adapter.iter_rows("test", include_labels=False)):
            if row_id < start_row:
                continue
            score = float(model.score(str(row["video_id"]), str(row["tab"])))
            if not math.isfinite(score):
                raise ValueError(f"non-finite score at row {row_id}")
            writer.writerow((row_id, row["user_id"], row["video_id"], score))
            rows += 1
            if state_file is not None and rows % checkpoint_every == 0:
                writer.sync()
                _write_state(state_file, {
                    "identity": identity, "stage": "stream", "rows_completed": rows,
                    "bytes_written": writer.bytes_written, "content_sha256": writer.content_sha256,
                })
                checkpoints += 1
                if progress_hook is not None:
                    progress_hook(ScaleProgress("output", "stream", rows))
        writer.sync()
        final_digest = writer.content_sha256
    partial_path.replace(output_path)
    if state_file is not None:
        _write_state(state_file, {
            "identity": identity, "stage": "complete", "rows_completed": rows,
            "bytes_written": writer.bytes_written, "content_sha256": final_digest,
        })
        if progress_hook is not None:
            progress_hook(ScaleProgress("output", "complete", rows))
    return {
        "output": str(output_path), "rows": float(rows), "model_sha256": identity["model_sha256"],
        "output_sha256": final_digest, "resumed_from_row": float(resumed_from),
        "checkpoints_written": float(checkpoints),
    }


def rescore_frozen_scale_model(
    *,
    model_path: str | Path,
    variant: str,
    data_dir: str | Path,
    evaluator_path: str | Path,
    shards: int = 256,
    scratch_dir: str | Path | None = None,
    item_weight: float | None = None,
) -> dict[str, float | str]:
    """Re-evaluate a frozen model with an optional declared item×tab blend weight."""
    started = perf_counter(); model = load_scale_model(model_path)
    if item_weight is not None:
        if not isinstance(model, TabConditionedHashedPopularity):
            raise ValueError("item_weight override requires a frozen item_tab scale model")
        if not 0 <= item_weight <= 1:
            raise ValueError("item_weight must be in [0, 1]")
        model = replace(model, item_weight=item_weight)
    scale = ScaleArtifactAdapter(variant, Path(data_dir))
    spec = BenchmarkSpec(benchmark_id=f"kuairand-{variant}", profile_id="bonus-reference-unconfirmed-long-view-gauc-ndcg5-v1", label="long_view", metrics=("GAUC", "nDCG@5", "primary"), evaluator_path=str(evaluator_path), evaluator_sha256=hash_file(evaluator_path), source_note="Interpretation - not explicit organizer wording: the Starter Kit evaluator is used for internal bonus-scale validation; no organizer bonus baseline, threshold, or submission procedure has been supplied.")
    metrics = _score_validation_sharded(adapter=scale, evaluator=BenchmarkAdapter.from_organizer_file(spec), model=model, shards=shards, scratch_dir=scratch_dir)
    metrics.update({"model_sha256": hash_file(model_path), "item_weight": float(model.item_weight) if isinstance(model, TabConditionedHashedPopularity) else -1.0, "wall_seconds": perf_counter() - started})
    return metrics


def fit_streaming_popularity(adapter: ScaleArtifactAdapter) -> StreamingPopularity:
    positives: dict[str, int] = defaultdict(int)
    totals: dict[str, int] = defaultdict(int)
    total_positive = total_rows = 0
    for row in adapter.iter_rows("train", include_labels=True):
        video_id = str(row["video_id"]); label = int(row["long_view"] != "0")
        positives[video_id] += label; totals[video_id] += 1; total_positive += label; total_rows += 1
    if not total_rows: raise ValueError("training split is empty")
    return StreamingPopularity(dict(positives), dict(totals), total_positive / total_rows)


def fit_hashed_streaming_popularity(adapter: ScaleArtifactAdapter, *, bits: int) -> HashedStreamingPopularity:
    """Fit a collision-tolerant fixed-size table without retaining item IDs."""
    if not 12 <= bits <= 27:
        raise ValueError("hash bits must be in [12, 27] to preserve a bounded-memory run")
    slots = 1 << bits
    positives = np.zeros(slots, dtype=np.uint32)
    totals = np.zeros(slots, dtype=np.uint32)
    total_positive = total_rows = 0
    mask = slots - 1
    for row in adapter.iter_rows("train", include_labels=True):
        bucket = zlib.crc32(str(row["video_id"]).encode("utf-8")) & mask
        label = int(row["long_view"] != "0")
        # The 27K artifact is far below uint32's per-bucket range at the
        # configured sizes; explicit arithmetic keeps the memory bound clear.
        positives[bucket] += label
        totals[bucket] += 1
        total_positive += label
        total_rows += 1
    if not total_rows:
        raise ValueError("training split is empty")
    return HashedStreamingPopularity(positives, totals, total_positive / total_rows, bits)


def fit_tab_conditioned_hashed_popularity(
    adapter: ScaleArtifactAdapter, *, bits: int, item_weight: float,
) -> TabConditionedHashedPopularity:
    """Fit item and item×tab tables from training rows only."""
    if not 12 <= bits <= 27:
        raise ValueError("hash bits must be in [12, 27] to preserve a bounded-memory run")
    if not 0 <= item_weight <= 1:
        raise ValueError("item_weight must be in [0, 1]")
    slots = 1 << bits
    item_positives = np.zeros(slots, dtype=np.uint32); item_totals = np.zeros(slots, dtype=np.uint32)
    tab_positives = np.zeros(slots, dtype=np.uint32); tab_totals = np.zeros(slots, dtype=np.uint32)
    total_positive = total_rows = 0; mask = slots - 1
    for row in adapter.iter_rows("train", include_labels=True):
        video_id = str(row["video_id"]); label = int(row["long_view"] != "0")
        item_bucket = zlib.crc32(video_id.encode("utf-8")) & mask
        tab_bucket = zlib.crc32(f"{video_id}\x1f{row['tab']}".encode("utf-8")) & mask
        item_positives[item_bucket] += label; item_totals[item_bucket] += 1
        tab_positives[tab_bucket] += label; tab_totals[tab_bucket] += 1
        total_positive += label; total_rows += 1
    if not total_rows:
        raise ValueError("training split is empty")
    return TabConditionedHashedPopularity(
        item_positives, item_totals, tab_positives, tab_totals, total_positive / total_rows, bits, item_weight,
    )


def _user_stats(users: list[str], labels: list[int]) -> tuple[int, int]:
    """Return (user count, GAUC positive-weight denominator) for one shard."""
    counts: dict[str, list[int]] = {}
    for user_id, label in zip(users, labels):
        state = counts.setdefault(user_id, [0, 0])
        state[0] += 1
        state[1] += label
    return len(counts), sum(positive for total, positive in counts.values() if 0 < positive < total)


def _shard_index(user_id: str, shards: int) -> int:
    return zlib.crc32(user_id.encode("utf-8")) % shards


@dataclass(slots=True)
class _ShardAccumulator:
    """Cross-shard aggregation of organizer-evaluated, user-consistent shards.

    nDCG is weighted by user count and GAUC by the positives in discriminative
    users, matching the supplied evaluator.  Holding the running totals in one
    serializable object is what lets a long 27K validation resume mid-pass.
    """

    gauc_numerator: float = 0.0
    gauc_denominator: int = 0
    ndcg_numerator: float = 0.0
    total_users: int = 0

    def add_shard(self, evaluator: BenchmarkAdapter, shard_path: Path) -> None:
        users: list[str] = []
        labels: list[int] = []
        scores: list[float] = []
        with shard_path.open(newline="", encoding="utf-8") as handle:
            for user_id, label, score in csv.reader(handle):
                users.append(user_id)
                labels.append(int(label))
                scores.append(float(score))
        if not users:
            return
        result = evaluator.score_development("valid", users, labels, scores)
        user_count, shard_gauc_weight = _user_stats(users, labels)
        self.total_users += user_count
        self.ndcg_numerator += result["nDCG@5"] * user_count
        if shard_gauc_weight:
            self.gauc_numerator += result["GAUC"] * shard_gauc_weight
            self.gauc_denominator += shard_gauc_weight

    def metrics(self, valid_rows: int) -> dict[str, float]:
        gauc = self.gauc_numerator / self.gauc_denominator if self.gauc_denominator else 0.5
        ndcg = self.ndcg_numerator / self.total_users if self.total_users else 0.0
        return {
            "GAUC": gauc,
            "nDCG@5": ndcg,
            "primary": (gauc + ndcg) / 2.0,
            "users": float(self.total_users),
            "rows": float(valid_rows),
        }

    def to_dict(self) -> dict[str, float | int]:
        return {
            "gauc_numerator": self.gauc_numerator,
            "gauc_denominator": self.gauc_denominator,
            "ndcg_numerator": self.ndcg_numerator,
            "total_users": self.total_users,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "_ShardAccumulator":
        return cls(
            float(payload["gauc_numerator"]),
            int(payload["gauc_denominator"]),
            float(payload["ndcg_numerator"]),
            int(payload["total_users"]),
        )


def _score_validation_sharded(
    *,
    adapter: ScaleArtifactAdapter,
    evaluator: BenchmarkAdapter,
    model: PopularityScorer,
    shards: int,
    scratch_dir: str | Path | None,
) -> dict[str, float]:
    """Score validation without ever splitting a user's impressions.

    Each shard delegates its local metric calculation to the supplied organizer
    evaluator.  The only cross-shard operation is the documented aggregation:
    nDCG is weighted by user count, while GAUC is weighted by the number of
    positives in discriminative users.  This matches the supplied evaluator's
    implementation and is regression-tested against an unsharded call.
    """
    if shards < 2:
        raise ValueError("at least two user shards are required for bounded validation")
    base = Path(scratch_dir) if scratch_dir else None
    if base:
        base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"kuairand-{adapter.variant}-valid-", dir=base) as raw_dir:
        root = Path(raw_dir)
        handles = [(root / f"{index:04d}.csv").open("w", newline="", encoding="utf-8") for index in range(shards)]
        writers = [csv.writer(handle) for handle in handles]
        valid_rows = 0
        try:
            for row in adapter.iter_rows("valid", include_labels=True):
                user_id = str(row["user_id"])
                writers[_shard_index(user_id, shards)].writerow(
                    (user_id, int(row["long_view"] != "0"), repr(model.score(str(row["video_id"]), str(row["tab"]))))
                )
                valid_rows += 1
        finally:
            for handle in handles:
                handle.close()

        accumulator = _ShardAccumulator()
        for shard_path in sorted(root.glob("*.csv")):
            accumulator.add_shard(evaluator, shard_path)

    return accumulator.metrics(valid_rows)


def run_streaming_popularity(
    *,
    variant: str,
    data_dir: str | Path,
    evaluator_path: str | Path,
    hash_bits: int | None = None,
    shards: int = 256,
    scratch_dir: str | Path | None = None,
    feature_mode: str = "item",
    item_weight: float = 0.5,
    model_output: str | Path | None = None,
) -> dict[str, float | str]:
    """Train on a stream and score only the official validation date range."""
    started = perf_counter(); scale = ScaleArtifactAdapter(variant, Path(data_dir))
    spec = BenchmarkSpec(benchmark_id=f"kuairand-{variant}", profile_id="bonus-reference-unconfirmed-long-view-gauc-ndcg5-v1", label="long_view", metrics=("GAUC", "nDCG@5", "primary"), evaluator_path=str(evaluator_path), evaluator_sha256=hash_file(evaluator_path), source_note="Interpretation - not explicit organizer wording: the Starter Kit evaluator is used for internal bonus-scale validation; no organizer bonus baseline, threshold, or submission procedure has been supplied.")
    evaluator = BenchmarkAdapter.from_organizer_file(spec)
    effective_bits = 24 if variant == "27k" and hash_bits is None else hash_bits
    if feature_mode not in {"item", "item_tab"}:
        raise ValueError("feature_mode must be item or item_tab")
    if feature_mode == "item_tab" and effective_bits is None:
        raise ValueError("item_tab mode requires an explicit bounded hash table")
    if effective_bits is None:
        model: PopularityScorer = fit_streaming_popularity(scale)
        model_slots = float(len(model.totals))
        model_hash_bits = -1.0
    elif feature_mode == "item":
        model = fit_hashed_streaming_popularity(scale, bits=effective_bits)
        model_slots = float(len(model.totals))
        model_hash_bits = float(effective_bits)
    else:
        model = fit_tab_conditioned_hashed_popularity(scale, bits=effective_bits, item_weight=item_weight)
        model_slots = float(2 * len(model.item_totals))
        model_hash_bits = float(effective_bits)
    model_sha256: str | None = None
    if model_output is not None:
        checkpoint = save_scale_model(model, model_output)
        model_sha256 = hash_file(checkpoint)
    metrics = _score_validation_sharded(
        adapter=scale, evaluator=evaluator, model=model, shards=shards, scratch_dir=scratch_dir,
    )
    metrics.update({"model_slots": model_slots, "model_hash_bits": model_hash_bits, "item_weight": float(item_weight), "wall_seconds": perf_counter() - started})
    if model_sha256 is not None:
        metrics["model_sha256"] = model_sha256
    return metrics


def score_scale_validation_resumable(
    *,
    model_path: str | Path,
    variant: str,
    data_dir: str | Path,
    evaluator_path: str | Path,
    state_dir: str | Path,
    shards: int = 256,
    item_weight: float | None = None,
    data_fingerprint: str | None = None,
    checkpoint_every: int = 100_000,
    progress_hook: Callable[[ScaleProgress], None] | None = None,
    resume: bool = True,
) -> dict[str, float | str]:
    """Score a frozen scale model on official validation, resumably.

    The pass has two stages.  `stream` writes user-consistent shards from the
    validation date range; `aggregate` delegates each shard to the organizer
    evaluator and accumulates the documented cross-shard weighting.  Both are
    checkpointed, so an interrupted 27K validation continues instead of
    restarting.  Shard scratch is verified by recorded byte length rather than
    a digest: it is internal, append-only, and fully reconstructible, whereas
    the published output in `generate_scale_submission_resumable` gets the
    stronger content check.

    Validation only ever reads the `valid` split.  Test labels are never
    requested here, and the adapter refuses them independently.
    """
    if shards < 2:
        raise ValueError("at least two user shards are required for bounded validation")
    if checkpoint_every < 1:
        raise ValueError("checkpoint_every must be at least one row")
    started = perf_counter()
    model_path = Path(model_path)
    model = load_scale_model(model_path)
    if item_weight is not None:
        if not isinstance(model, TabConditionedHashedPopularity):
            raise ValueError("item_weight override requires a frozen item_tab scale model")
        if not 0 <= item_weight <= 1:
            raise ValueError("item_weight must be in [0, 1]")
        model = replace(model, item_weight=item_weight)
    adapter = ScaleArtifactAdapter(variant, Path(data_dir))
    state_dir = Path(state_dir)
    shard_dir = state_dir / "shards"
    state_file = state_dir / "progress.json"

    identity = _run_identity(
        operation="validation",
        adapter=adapter,
        split="valid",
        model_path=model_path,
        target=state_dir,
        configuration={
            "operation": "validation",
            "shards": shards,
            "item_weight": float(model.item_weight) if isinstance(model, TabConditionedHashedPopularity) else None,
        },
        data_fingerprint=data_fingerprint,
        evaluator_path=evaluator_path,
    )
    spec = BenchmarkSpec(
        benchmark_id=f"kuairand-{variant}",
        profile_id="bonus-reference-unconfirmed-long-view-gauc-ndcg5-v1",
        label="long_view",
        metrics=("GAUC", "nDCG@5", "primary"),
        evaluator_path=str(evaluator_path),
        evaluator_sha256=identity["evaluator_sha256"],
        source_note=(
            "Interpretation - not explicit organizer wording: the Starter Kit evaluator is used "
            "for internal bonus-scale validation; no organizer bonus baseline, threshold, or "
            "submission procedure has been supplied."
        ),
    )
    # Guard the split name against the frozen contract as well as the adapter.
    spec.assert_development_split("valid")
    evaluator = BenchmarkAdapter.from_organizer_file(spec)

    state = _load_state(state_file, identity) if resume else None
    if state is not None and state.get("stage") == "complete":
        metrics = {str(key): float(value) for key, value in state["metrics"].items()}
        metrics.update({
            "model_sha256": identity["model_sha256"], "resumed_stage": "complete",
            "wall_seconds": perf_counter() - started,
        })
        return metrics

    shard_dir.mkdir(parents=True, exist_ok=True)
    shard_paths = [shard_dir / f"{index:04d}.csv" for index in range(shards)]
    valid_rows = 0
    resumed_from = 0
    if state is not None and state.get("stage") == "stream":
        recorded = [int(length) for length in state["shard_bytes"]]
        if len(recorded) != shards:
            raise ScaleResumeMismatch("recorded shard count does not match the requested shard count")
        for path, length in zip(shard_paths, recorded):
            if length and not path.is_file():
                raise ScaleResumeMismatch(f"{path} is missing but its progress records {length} bytes")
            if path.is_file():
                _truncate_to(path, length)
        valid_rows = resumed_from = int(state["rows_completed"])

    if state is None or state.get("stage") == "stream":
        start_row = valid_rows
        handles = [path.open("a" if start_row else "w", newline="", encoding="utf-8") for path in shard_paths]
        writers = [csv.writer(handle) for handle in handles]
        try:
            for row_index, row in enumerate(adapter.iter_rows("valid", include_labels=True)):
                if row_index < start_row:
                    continue
                user_id = str(row["user_id"])
                writers[_shard_index(user_id, shards)].writerow(
                    (user_id, int(row["long_view"] != "0"), repr(model.score(str(row["video_id"]), str(row["tab"]))))
                )
                valid_rows += 1
                if valid_rows % checkpoint_every == 0:
                    for handle in handles:
                        handle.flush()
                        os.fsync(handle.fileno())
                    _write_state(state_file, {
                        "identity": identity, "stage": "stream", "rows_completed": valid_rows,
                        "shard_bytes": [path.stat().st_size for path in shard_paths],
                    })
                    if progress_hook is not None:
                        progress_hook(ScaleProgress("validation", "stream", valid_rows))
        finally:
            for handle in handles:
                handle.flush()
                os.fsync(handle.fileno())
                handle.close()
        state = {
            "identity": identity, "stage": "aggregate", "rows_completed": valid_rows,
            "completed_shards": [], "accumulator": _ShardAccumulator().to_dict(),
        }
        _write_state(state_file, state)

    accumulator = _ShardAccumulator.from_dict(state["accumulator"])
    completed = list(state["completed_shards"])
    valid_rows = int(state["rows_completed"])
    for shard_path in sorted(shard_dir.glob("*.csv")):
        if shard_path.name in completed:
            continue
        accumulator.add_shard(evaluator, shard_path)
        completed.append(shard_path.name)
        _write_state(state_file, {
            "identity": identity, "stage": "aggregate", "rows_completed": valid_rows,
            "completed_shards": completed, "accumulator": accumulator.to_dict(),
        })
        if progress_hook is not None:
            progress_hook(ScaleProgress("validation", "aggregate", valid_rows, len(completed)))

    metrics = accumulator.metrics(valid_rows)
    _write_state(state_file, {
        "identity": identity, "stage": "complete", "rows_completed": valid_rows,
        "completed_shards": completed, "accumulator": accumulator.to_dict(), "metrics": metrics,
    })
    # Scratch shards are reconstructible; the completed record keeps the result.
    shutil.rmtree(shard_dir, ignore_errors=True)
    result: dict[str, float | str] = dict(metrics)
    result.update({
        "model_sha256": identity["model_sha256"],
        "item_weight": float(model.item_weight) if isinstance(model, TabConditionedHashedPopularity) else -1.0,
        "resumed_from_row": float(resumed_from),
        "wall_seconds": perf_counter() - started,
    })
    return result

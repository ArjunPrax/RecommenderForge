"""Bounded-memory item-popularity baselines for KuaiRand bonus artifacts.

The exact dictionary model is useful for 1K.  It is deliberately not used by
default on 27K: a Python dictionary of the full 27K item universe is an
unbounded laptop-memory commitment.  The 27K route uses a fixed-size, stable
hash table and evaluates validation in user-consistent shards.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Protocol
import csv
import tempfile
import zlib

import numpy as np

from .benchmark import BenchmarkAdapter
from .contracts import BenchmarkSpec, hash_file
from .scale import ScaleArtifactAdapter


@dataclass(frozen=True, slots=True)
class StreamingPopularity:
    positives: dict[str, int]
    totals: dict[str, int]
    global_rate: float

    def score(self, video_id: str) -> float:
        total = self.totals.get(video_id, 0)
        # Smoothed rate is stable for one-off videos.
        return (self.positives.get(video_id, 0) + 5 * self.global_rate) / (total + 5)


class PopularityScorer(Protocol):
    global_rate: float

    def score(self, video_id: str) -> float: ...


@dataclass(frozen=True, slots=True)
class HashedStreamingPopularity:
    """Fixed-memory popularity table using a cross-run-stable item hash."""

    positives: np.ndarray
    totals: np.ndarray
    global_rate: float
    bits: int

    def _bucket(self, video_id: str) -> int:
        return zlib.crc32(video_id.encode("utf-8")) & ((1 << self.bits) - 1)

    def score(self, video_id: str) -> float:
        bucket = self._bucket(video_id)
        return (float(self.positives[bucket]) + 5 * self.global_rate) / (float(self.totals[bucket]) + 5)


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
                    (user_id, int(row["long_view"] != "0"), repr(model.score(str(row["video_id"]))))
                )
                valid_rows += 1
        finally:
            for handle in handles:
                handle.close()

        gauc_numerator = 0.0
        gauc_denominator = 0
        ndcg_numerator = 0.0
        total_users = 0
        for shard_path in root.glob("*.csv"):
            users: list[str] = []
            labels: list[int] = []
            scores: list[float] = []
            with shard_path.open(newline="", encoding="utf-8") as handle:
                for user_id, label, score in csv.reader(handle):
                    users.append(user_id)
                    labels.append(int(label))
                    scores.append(float(score))
            if not users:
                continue
            result = evaluator.score_development("valid", users, labels, scores)
            user_count, shard_gauc_weight = _user_stats(users, labels)
            total_users += user_count
            ndcg_numerator += result["nDCG@5"] * user_count
            if shard_gauc_weight:
                gauc_numerator += result["GAUC"] * shard_gauc_weight
                gauc_denominator += shard_gauc_weight

    gauc = gauc_numerator / gauc_denominator if gauc_denominator else 0.5
    ndcg = ndcg_numerator / total_users if total_users else 0.0
    return {
        "GAUC": gauc,
        "nDCG@5": ndcg,
        "primary": (gauc + ndcg) / 2.0,
        "users": float(total_users),
        "rows": float(valid_rows),
    }


def run_streaming_popularity(
    *,
    variant: str,
    data_dir: str | Path,
    evaluator_path: str | Path,
    hash_bits: int | None = None,
    shards: int = 256,
    scratch_dir: str | Path | None = None,
) -> dict[str, float]:
    """Train on a stream and score only the official validation date range."""
    started = perf_counter(); scale = ScaleArtifactAdapter(variant, Path(data_dir))
    spec = BenchmarkSpec(benchmark_id=f"kuairand-{variant}", profile_id="provisional-long-view-gauc-ndcg5-v1", label="long_view", metrics=("GAUC", "nDCG@5", "primary"), evaluator_path=str(evaluator_path), evaluator_sha256=hash_file(evaluator_path), source_note="Interpretation - provisional starter evaluator applied to bonus artifact pending organizer contract.")
    evaluator = BenchmarkAdapter.from_organizer_file(spec)
    effective_bits = 24 if variant == "27k" and hash_bits is None else hash_bits
    if effective_bits is None:
        model: PopularityScorer = fit_streaming_popularity(scale)
        model_slots = float(len(model.totals))
        model_hash_bits = -1.0
    else:
        model = fit_hashed_streaming_popularity(scale, bits=effective_bits)
        model_slots = float(len(model.totals))
        model_hash_bits = float(effective_bits)
    metrics = _score_validation_sharded(
        adapter=scale, evaluator=evaluator, model=model, shards=shards, scratch_dir=scratch_dir,
    )
    metrics.update({"model_slots": model_slots, "model_hash_bits": model_hash_bits, "wall_seconds": perf_counter() - started})
    return metrics

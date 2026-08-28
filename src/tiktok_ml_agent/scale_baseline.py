"""Bounded-memory item-popularity baselines for KuaiRand bonus artifacts.

The exact dictionary model is useful for 1K.  It is deliberately not used by
default on 27K: a Python dictionary of the full 27K item universe is an
unbounded laptop-memory commitment.  The 27K route uses a fixed-size, stable
hash table and evaluates validation in user-consistent shards.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter
from typing import Protocol
import csv
import math
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


def generate_scale_submission(
    *, model_path: str | Path, variant: str, data_dir: str | Path, output_path: str | Path,
) -> dict[str, float | str]:
    """Stream a feature-only starter-schema output from a frozen scale model."""
    model_path = Path(model_path); model = load_scale_model(model_path)
    adapter = ScaleArtifactAdapter(variant, Path(data_dir))
    output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = output_path.with_name(f"{output_path.name}.partial")
    rows = 0
    with partial_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(("row_id", "user_id", "video_id", "score"))
        for row_id, row in enumerate(adapter.iter_rows("test", include_labels=False)):
            score = float(model.score(str(row["video_id"]), str(row["tab"])))
            if not math.isfinite(score):
                raise ValueError(f"non-finite score at row {row_id}")
            writer.writerow((row_id, row["user_id"], row["video_id"], score))
            rows += 1
    partial_path.replace(output_path)
    return {"output": str(output_path), "rows": float(rows), "model_sha256": hash_file(model_path)}


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
    spec = BenchmarkSpec(benchmark_id=f"kuairand-{variant}", profile_id="provisional-long-view-gauc-ndcg5-v1", label="long_view", metrics=("GAUC", "nDCG@5", "primary"), evaluator_path=str(evaluator_path), evaluator_sha256=hash_file(evaluator_path), source_note="Interpretation - provisional starter evaluator applied to bonus artifact pending organizer contract.")
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
    feature_mode: str = "item",
    item_weight: float = 0.5,
    model_output: str | Path | None = None,
) -> dict[str, float | str]:
    """Train on a stream and score only the official validation date range."""
    started = perf_counter(); scale = ScaleArtifactAdapter(variant, Path(data_dir))
    spec = BenchmarkSpec(benchmark_id=f"kuairand-{variant}", profile_id="provisional-long-view-gauc-ndcg5-v1", label="long_view", metrics=("GAUC", "nDCG@5", "primary"), evaluator_path=str(evaluator_path), evaluator_sha256=hash_file(evaluator_path), source_note="Interpretation - provisional starter evaluator applied to bonus artifact pending organizer contract.")
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

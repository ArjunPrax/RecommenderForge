"""Streaming item-popularity baseline for official KuaiRand-1K/27K artifacts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

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


def fit_streaming_popularity(adapter: ScaleArtifactAdapter) -> StreamingPopularity:
    positives: dict[str, int] = defaultdict(int)
    totals: dict[str, int] = defaultdict(int)
    total_positive = total_rows = 0
    for row in adapter.iter_rows("train", include_labels=True):
        video_id = str(row["video_id"]); label = int(row["long_view"] != "0")
        positives[video_id] += label; totals[video_id] += 1; total_positive += label; total_rows += 1
    if not total_rows: raise ValueError("training split is empty")
    return StreamingPopularity(dict(positives), dict(totals), total_positive / total_rows)


def run_streaming_popularity(
    *, variant: str, data_dir: str | Path, evaluator_path: str | Path,
) -> dict[str, float]:
    """Train on a stream and score only the official validation date range."""
    started = perf_counter(); scale = ScaleArtifactAdapter(variant, Path(data_dir))
    spec = BenchmarkSpec(benchmark_id=f"kuairand-{variant}", profile_id="provisional-long-view-gauc-ndcg5-v1", label="long_view", metrics=("GAUC", "nDCG@5", "primary"), evaluator_path=str(evaluator_path), evaluator_sha256=hash_file(evaluator_path), source_note="Interpretation - provisional starter evaluator applied to bonus artifact pending organizer contract.")
    evaluator = BenchmarkAdapter.from_organizer_file(spec); model = fit_streaming_popularity(scale)
    users: list[str] = []; labels: list[int] = []; scores: list[float] = []
    for row in scale.iter_rows("valid", include_labels=True):
        users.append(str(row["user_id"])); labels.append(int(row["long_view"] != "0")); scores.append(model.score(str(row["video_id"])))
    metrics = evaluator.score_development("valid", users, labels, scores)
    metrics.update({"train_unique_items": float(len(model.totals)), "valid_rows": float(len(users)), "wall_seconds": perf_counter() - started})
    return metrics

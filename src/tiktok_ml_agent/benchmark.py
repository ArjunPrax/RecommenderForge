"""Organizer-evaluator delegation and hidden-test access controls."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, Iterable, Sequence

from .contracts import BenchmarkSpec, TestAccessError


def load_organizer_evaluator(path: str | Path) -> Callable[..., dict[str, float]]:
    """Load the organizer's `evaluate` function without copying its metric logic."""
    path = Path(path)
    spec = importlib.util.spec_from_file_location("organizer_evaluator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load evaluator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    evaluator = getattr(module, "evaluate", None)
    if not callable(evaluator):
        raise AttributeError(f"{path} has no callable evaluate function")
    return evaluator


@dataclass(slots=True)
class BenchmarkAdapter:
    """Only exposes development scoring to research candidates."""

    spec: BenchmarkSpec
    evaluator: Callable[[Sequence[str], Sequence[int], Sequence[float]], dict[str, float]]

    @classmethod
    def from_organizer_file(cls, spec: BenchmarkSpec) -> "BenchmarkAdapter":
        if not spec.evaluator_path:
            raise ValueError("BenchmarkSpec requires evaluator_path")
        return cls(spec=spec, evaluator=load_organizer_evaluator(spec.evaluator_path))

    def score_development(
        self,
        split: str,
        user_ids: Sequence[str],
        labels: Sequence[int],
        scores: Sequence[float],
    ) -> dict[str, float]:
        self.spec.assert_development_split(split)
        if len(user_ids) != len(labels) or len(labels) != len(scores):
            raise ValueError("user_ids, labels, and scores must have equal length")
        result = self.evaluator(user_ids, labels, scores)
        if "primary" not in result:
            raise ValueError("organizer evaluator must return a primary metric")
        return {str(key): float(value) for key, value in result.items()}

    def forbid_test_labels(self, split: str, include_labels: bool) -> None:
        if split == self.spec.test_split and include_labels:
            raise TestAccessError("candidate code may not retrieve hidden-test labels")

    def validate_submission_rows(
        self,
        rows: Iterable[tuple[str, str]],
        submission: Iterable[tuple[int, str, str, float]],
    ) -> None:
        """Validate alignment only; this deliberately performs no test-label scoring."""
        expected_rows = list(rows)
        actual_rows = list(submission)
        if len(expected_rows) != len(actual_rows):
            raise ValueError("submission row count does not match evaluation rows")
        for index, ((user_id, video_id), (row_id, out_user, out_video, score)) in enumerate(
            zip(expected_rows, actual_rows)
        ):
            if row_id != index:
                raise ValueError("row_id must be zero-based and strictly increasing")
            if (user_id, video_id) != (out_user, out_video):
                raise ValueError("submission user/video fields are misaligned")
            if not isinstance(score, (float, int)) or score != score or abs(float(score)) == float("inf"):
                raise ValueError("submission scores must be finite numeric values")

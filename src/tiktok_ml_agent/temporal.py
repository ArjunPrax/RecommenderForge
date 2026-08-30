"""Validation-window stability diagnostics; never a proxy rejection gate."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .kuairand import KuaiRandRow


def temporal_primary_windows(
    rows: list[KuaiRandRow], scores: np.ndarray, score: Callable[[list[str], list[int], list[float]], dict[str, float]]
) -> dict[str, float]:
    """Score early/late official-validation windows for drift reporting only."""
    if len(rows) != len(scores):
        raise ValueError("validation rows and scores must align")
    windows = {
        "valid_early": [index for index, row in enumerate(rows) if row.date <= 20220425],
        "valid_late": [index for index, row in enumerate(rows) if row.date >= 20220426],
    }
    result: dict[str, float] = {}
    for name, indices in windows.items():
        if not indices:
            raise ValueError(f"{name} contains no rows")
        selected = [rows[index] for index in indices]
        metrics = score(
            [row.user_id for row in selected],
            [int(row.label) for row in selected if row.label is not None],
            [float(scores[index]) for index in indices],
        )
        result[f"{name}_primary"] = metrics["primary"]
    result["valid_temporal_gap"] = result["valid_early_primary"] - result["valid_late_primary"]
    return result

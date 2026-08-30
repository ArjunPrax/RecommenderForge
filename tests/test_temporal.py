from __future__ import annotations

import unittest

import numpy as np

from tiktok_ml_agent.kuairand import KuaiRandRow
from tiktok_ml_agent.temporal import temporal_primary_windows


def row(date: int, label: int) -> KuaiRandRow:
    return KuaiRandRow(date, 1, "u", "v", "a", "0", 10.0, label)


class TemporalWindowTests(unittest.TestCase):
    def test_scores_early_and_late_windows(self) -> None:
        def score(users, labels, scores):
            return {"primary": sum(scores) / len(scores)}
        result = temporal_primary_windows(
            [row(20220422, 1), row(20220428, 0)], np.asarray([0.8, 0.4]), score
        )
        self.assertEqual(result["valid_early_primary"], 0.8)
        self.assertEqual(result["valid_late_primary"], 0.4)
        self.assertEqual(result["valid_temporal_gap"], 0.4)


if __name__ == "__main__":
    unittest.main()

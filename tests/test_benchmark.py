from __future__ import annotations

import unittest

from tiktok_ml_agent.benchmark import BenchmarkAdapter
from tiktok_ml_agent.contracts import BenchmarkSpec, TestAccessError


def evaluator(users, labels, scores):
    return {"primary": sum(float(score) for score in scores) / len(scores)}


class BenchmarkAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = BenchmarkSpec(
            benchmark_id="fixture",
            profile_id="fixture-v1",
            label="label",
            metrics=("primary",),
        )
        self.adapter = BenchmarkAdapter(self.spec, evaluator)

    def test_valid_development_scoring_delegates(self) -> None:
        result = self.adapter.score_development("valid", ["u"], [1], [0.75])
        self.assertEqual(result["primary"], 0.75)

    def test_test_scoring_fails_closed(self) -> None:
        with self.assertRaises(TestAccessError):
            self.adapter.score_development("test", ["u"], [1], [0.75])
        with self.assertRaises(TestAccessError):
            self.adapter.forbid_test_labels("test", include_labels=True)

    def test_submission_alignment_does_not_need_labels(self) -> None:
        self.adapter.validate_submission_rows(
            [("u1", "v1"), ("u1", "v1")],
            [(0, "u1", "v1", 0.1), (1, "u1", "v1", 0.2)],
        )
        with self.assertRaises(ValueError):
            self.adapter.validate_submission_rows(
                [("u1", "v1")], [(1, "u1", "v1", 0.1)]
            )

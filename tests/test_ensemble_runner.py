from __future__ import annotations

import unittest

import numpy as np

from tiktok_ml_agent.ensemble_runner import _percentile_ranks


class EnsembleRunnerTests(unittest.TestCase):
    def test_percentile_rank_is_monotonic(self) -> None:
        ranks = _percentile_ranks(np.asarray([3.0, 1.0, 2.0]))
        np.testing.assert_allclose(ranks, np.asarray([1.0, 0.0, 0.5]))


if __name__ == "__main__":
    unittest.main()

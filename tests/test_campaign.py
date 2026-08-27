from __future__ import annotations

import unittest

from tiktok_ml_agent.campaign import CampaignConvergence


class CampaignConvergenceTests(unittest.TestCase):
    def test_siblings_are_one_batch_and_epsilon_resets_stagnation(self) -> None:
        tracker = CampaignConvergence(0.60, epsilon=0.002, patience=3)
        tracker.add_batch("b1", [("a", 0.601), ("b", 0.6015)])
        tracker.add_batch("b2", [("c", 0.603)])
        status = tracker.add_batch("b3", [("d", 0.6035)])
        self.assertEqual(status.stagnation, 1)
        self.assertEqual(status.best_run_id, "d")
        self.assertFalse(status.converged)
        tracker.add_batch("b4", [("e", 0.6034)])
        status = tracker.add_batch("b5", [("f", 0.6032)])
        self.assertTrue(status.converged)


if __name__ == "__main__":
    unittest.main()

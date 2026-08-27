from __future__ import annotations

import unittest

import numpy as np

from tiktok_ml_agent.ordering import within_user_ordering_change


class OrderingAuditTests(unittest.TestCase):
    def test_detects_a_changed_within_user_relation(self) -> None:
        result = within_user_ordering_change(
            ["u1", "u1", "u2", "u2"],
            np.asarray([0.9, 0.1, 0.8, 0.2]),
            np.asarray([0.1, 0.9, 0.7, 0.3]),
        )
        self.assertEqual(result["eligible_users"], 2)
        self.assertEqual(result["changed_users"], 1)
        self.assertEqual(result["changed_pairwise_relations"], 1)


if __name__ == "__main__":
    unittest.main()

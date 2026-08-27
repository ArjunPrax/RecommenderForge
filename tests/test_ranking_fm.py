from __future__ import annotations

import unittest

import numpy as np
import torch

from tiktok_ml_agent.ranking_fm import _exact_listwise_loss, _group_batches, _sample_bpr_pairs


class RankingObjectiveTests(unittest.TestCase):
    def test_bpr_pairs_never_cross_users(self) -> None:
        groups = [np.asarray([0, 1]), np.asarray([2, 3, 4])]
        labels = np.asarray([1, 0, 0, 1, 0])
        positives, negatives = _sample_bpr_pairs(groups, labels, np.random.default_rng(1))
        self.assertTrue(all((pos < 2) == (neg < 2) for pos, neg in zip(positives, negatives)))

    def test_group_batches_keep_complete_groups(self) -> None:
        groups = [np.asarray([0, 1]), np.asarray([2, 3, 4]), np.asarray([5])]
        batches = _group_batches(groups, 3)
        self.assertEqual([batch.tolist() for batch in batches], [[0, 1], [2, 3, 4], [5]])

    def test_exact_listwise_prefers_positive_at_top(self) -> None:
        labels = torch.tensor([1.0, 0.0, 1.0, 0.0])
        good = _exact_listwise_loss(torch.tensor([3.0, 0.0, 2.0, -1.0]), labels, [2, 2])
        bad = _exact_listwise_loss(torch.tensor([0.0, 3.0, -1.0, 2.0]), labels, [2, 2])
        self.assertLess(float(good), float(bad))

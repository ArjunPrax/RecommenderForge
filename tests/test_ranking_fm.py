from __future__ import annotations

import unittest

import numpy as np
import torch

from tiktok_ml_agent.ranking_fm import _exact_listwise_loss, _group_batches, _lambda_ndcg5_weights, _sample_bpr_pairs


class RankingObjectiveTests(unittest.TestCase):
    def test_bpr_pairs_never_cross_users(self) -> None:
        groups = [np.asarray([0, 1]), np.asarray([2, 3, 4])]
        labels = np.asarray([1, 0, 0, 1, 0])
        positives, negatives = _sample_bpr_pairs(groups, labels, np.random.default_rng(1))
        self.assertTrue(all((pos < 2) == (neg < 2) for pos, neg in zip(positives, negatives)))

    def test_bpr_can_draw_multiple_negatives_per_positive(self) -> None:
        groups = [np.asarray([0, 1, 2]), np.asarray([3, 4])]
        labels = np.asarray([1, 0, 0, 1, 0])
        positives, negatives = _sample_bpr_pairs(
            groups, labels, np.random.default_rng(0), negatives_per_positive=3
        )
        self.assertEqual(len(positives), 6)
        self.assertEqual(len(negatives), 6)

    def test_lambda_weights_prioritize_top_five_swaps(self) -> None:
        group = np.arange(7)
        labels = np.asarray([1, 0, 0, 0, 0, 0, 1])
        scores = np.asarray([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3])
        weights = _lambda_ndcg5_weights([group], labels, scores, np.asarray([0, 6]), np.asarray([1, 5]))
        self.assertGreater(weights[0], 0)
        self.assertEqual(weights[1], 0)

    def test_group_batches_keep_complete_groups(self) -> None:
        groups = [np.asarray([0, 1]), np.asarray([2, 3, 4]), np.asarray([5])]
        batches = _group_batches(groups, 3)
        self.assertEqual([batch.tolist() for batch in batches], [[0, 1], [2, 3, 4], [5]])

    def test_exact_listwise_prefers_positive_at_top(self) -> None:
        labels = torch.tensor([1.0, 0.0, 1.0, 0.0])
        good = _exact_listwise_loss(torch.tensor([3.0, 0.0, 2.0, -1.0]), labels, [2, 2])
        bad = _exact_listwise_loss(torch.tensor([0.0, 3.0, -1.0, 2.0]), labels, [2, 2])
        self.assertLess(float(good), float(bad))

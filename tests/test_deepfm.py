from __future__ import annotations

import unittest

import torch

from tiktok_ml_agent.deepfm import DeepFM


class DeepFMTests(unittest.TestCase):
    def test_logits_and_bpr_update_are_finite(self) -> None:
        model = DeepFM(20, field_count=3, k=4, hidden=8, seed=0)
        positive, negative = torch.tensor([[1, 2, 3]]), torch.tensor([[4, 5, 6]])
        loss = -torch.nn.functional.logsigmoid(model.logits(positive) - model.logits(negative)).mean()
        model.step_loss(loss)
        self.assertTrue(torch.isfinite(model.logits(positive)).all())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

import torch
from torch.nn import functional as functional

from tiktok_ml_agent.multitask_fm import MultiTaskFM


class MultiTaskFMTests(unittest.TestCase):
    def test_auxiliary_head_receives_a_gradient_update(self) -> None:
        model = MultiTaskFM(12, k=3, lr=0.01, seed=0, task_count=4)
        x = torch.tensor([[1, 3], [2, 4]], dtype=torch.int64)
        before = model.task_bias.detach().clone()
        loss = functional.binary_cross_entropy_with_logits(model.task_logits(x, 1), torch.tensor([1.0, 0.0]))
        model.step_loss(loss)
        self.assertNotEqual(float(before[1]), float(model.task_bias[1].detach()))
        self.assertEqual(float(before[0]), float(model.task_bias[0].detach()))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

import torch
from torch.nn import functional as functional

from tiktok_ml_agent.watchtime_fm import WatchTimeFM


class WatchTimeFMTests(unittest.TestCase):
    def test_watch_head_receives_a_gradient_update(self) -> None:
        model = WatchTimeFM(12, k=3, lr=0.01, seed=0)
        x = torch.tensor([[1, 3], [2, 4]], dtype=torch.int64)
        before = model.watch_bias.detach().clone()
        loss = functional.binary_cross_entropy_with_logits(model.watch_logits(x), torch.tensor([1.0, 0.0]))
        model.step_loss(loss)
        self.assertNotEqual(float(before), float(model.watch_bias.detach()))


if __name__ == "__main__":
    unittest.main()

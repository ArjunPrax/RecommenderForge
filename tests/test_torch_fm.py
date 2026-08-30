from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np
import torch

from tiktok_ml_agent.torch_fm import TorchFM


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "kuairand-starter-kit"


def organizer_fm():
    sys.path.insert(0, str(KIT))
    try:
        spec = importlib.util.spec_from_file_location("starter_baseline_test", KIT / "baseline.py")
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load starter baseline")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.FM
    finally:
        sys.path.remove(str(KIT))


@unittest.skipUnless((KIT / "baseline.py").is_file(), "requires local organizer baseline")
class TorchFMParityTests(unittest.TestCase):
    def test_fixed_weights_match_organizer_logits_and_loss(self) -> None:
        fm = organizer_fm()(12, k=4, lr=0.001, seed=7)
        port = TorchFM.from_numpy(fm)
        matrix = np.asarray([[0, 2, 4, 7, 10], [1, 3, 5, 8, 11]], dtype=np.int32)
        labels = np.asarray([1.0, 0.0], dtype=np.float32)
        numpy_logits = fm.logits(matrix)[0]
        torch_logits = port.logits(torch.from_numpy(matrix)).detach().numpy()
        self.assertTrue(np.allclose(numpy_logits, torch_logits, atol=1e-6))
        numpy_loss = -np.mean(
            labels * np.log(1 / (1 + np.exp(-numpy_logits)) + 1e-9)
            + (1 - labels) * np.log(1 - 1 / (1 + np.exp(-numpy_logits)) + 1e-9)
        )
        torch_loss = torch.nn.functional.binary_cross_entropy_with_logits(
            torch.from_numpy(torch_logits), torch.from_numpy(labels)
        ).item()
        self.assertAlmostEqual(numpy_loss, torch_loss, places=6)

    def test_one_update_matches_organizer_state(self) -> None:
        fm = organizer_fm()(12, k=4, lr=0.001, seed=3)
        port = TorchFM.from_numpy(fm)
        matrix = np.asarray([[0, 2, 4, 7, 10], [1, 3, 5, 8, 11], [0, 3, 5, 7, 11]], dtype=np.int32)
        labels = np.asarray([1.0, 0.0, 1.0], dtype=np.float32)
        fm.step(matrix, labels)
        port.step(torch.from_numpy(matrix), torch.from_numpy(labels))
        self.assertTrue(np.allclose(fm.V, port.V.detach().numpy(), atol=2e-6))
        self.assertTrue(np.allclose(fm.W, port.W.detach().numpy(), atol=2e-6))
        self.assertAlmostEqual(float(fm.b), float(port.b.detach()), places=6)

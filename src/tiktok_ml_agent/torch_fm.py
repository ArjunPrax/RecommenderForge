"""PyTorch port of the organizer FM with explicit optimizer parity controls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import torch
from torch import Tensor, nn
from torch.nn import functional as functional

from .baseline_runner import StarterFMConfig, _encode_train_validation
from .kuairand import KuaiRandPureAdapter


class TorchFM(nn.Module):
    """Factorization Machine matching starter-kit forward and Adam-like updates."""

    def __init__(self, dimension: int, k: int = 16, lr: float = 0.001, l2: float = 1e-6, seed: int = 0) -> None:
        super().__init__()
        generator = torch.Generator(device="cpu").manual_seed(seed)
        self.V = nn.Parameter(torch.randn((dimension, k), generator=generator, dtype=torch.float32) * 0.01)
        self.W = nn.Parameter(torch.zeros(dimension, dtype=torch.float32))
        self.b = nn.Parameter(torch.zeros((), dtype=torch.float32))
        self.lr, self.l2 = lr, l2
        self.register_buffer("mV", torch.zeros_like(self.V))
        self.register_buffer("vV", torch.zeros_like(self.V))
        self.register_buffer("mW", torch.zeros_like(self.W))
        self.register_buffer("vW", torch.zeros_like(self.W))
        self.register_buffer("t", torch.zeros((), dtype=torch.int64))

    @classmethod
    def from_numpy(cls, numpy_model: Any) -> "TorchFM":
        model = cls(
            numpy_model.V.shape[0],
            k=numpy_model.V.shape[1],
            lr=float(numpy_model.lr),
            l2=float(numpy_model.l2),
        )
        with torch.no_grad():
            model.V.copy_(torch.from_numpy(numpy_model.V))
            model.W.copy_(torch.from_numpy(numpy_model.W))
            model.b.copy_(torch.tensor(numpy_model.b, dtype=torch.float32))
            model.mV.copy_(torch.from_numpy(numpy_model.mV))
            model.vV.copy_(torch.from_numpy(numpy_model.vV))
            model.mW.copy_(torch.from_numpy(numpy_model.mW))
            model.vW.copy_(torch.from_numpy(numpy_model.vW))
            model.t.copy_(torch.tensor(numpy_model.t, dtype=torch.int64))
        return model

    def logits(self, x: Tensor) -> Tensor:
        embeddings = self.V[x]
        summed = embeddings.sum(dim=1)
        interactions = 0.5 * ((summed**2).sum(dim=1) - (embeddings**2).sum(dim=(1, 2)))
        return self.b + self.W[x].sum(dim=1) + interactions

    def step(self, x: Tensor, y: Tensor) -> float:
        logits = self.logits(x)
        loss = functional.binary_cross_entropy_with_logits(logits, y, reduction="mean")
        return self.step_loss(loss)

    def step_loss(self, loss: Tensor) -> float:
        """Apply the starter-kit optimizer semantics to an arbitrary differentiable loss."""
        self.zero_grad(set_to_none=True)
        loss.backward()
        if self.V.grad is None or self.W.grad is None or self.b.grad is None:
            raise RuntimeError("missing FM gradients")
        with torch.no_grad():
            grad_v = self.V.grad + self.l2 * self.V
            grad_w = self.W.grad + self.l2 * self.W
            self.t.add_(1)
            step = int(self.t.item())
            beta1, beta2, epsilon = 0.9, 0.999, 1e-8
            self.mV.mul_(beta1).add_(grad_v, alpha=1 - beta1)
            self.vV.mul_(beta2).addcmul_(grad_v, grad_v, value=1 - beta2)
            self.mW.mul_(beta1).add_(grad_w, alpha=1 - beta1)
            self.vW.mul_(beta2).addcmul_(grad_w, grad_w, value=1 - beta2)
            for parameter, first, second in ((self.V, self.mV, self.vV), (self.W, self.mW, self.vW)):
                first_hat = first / (1 - beta1**step)
                second_hat = second / (1 - beta2**step)
                parameter.addcdiv_(first_hat, second_hat.sqrt().add_(epsilon), value=-self.lr)
            self.b.add_(self.b.grad, alpha=-self.lr)
        return float(loss.detach().cpu())

    @torch.no_grad()
    def predict(self, x: Tensor, batch_size: int = 200_000) -> Tensor:
        return torch.cat([self.logits(x[index : index + batch_size]) for index in range(0, len(x), batch_size)])


def run_safe_torch_fm(
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    seed: int,
    config: StarterFMConfig | None = None,
    device: str = "cpu",
) -> dict[str, float]:
    """Train a pointwise PyTorch control on train/valid data only."""
    config = config or StarterFMConfig()
    if device != "cpu":
        raise ValueError("parity runs must use CPU; accelerator experiments are a later declared change")
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir)
    train = adapter.development_rows("train")
    valid = adapter.development_rows("valid")
    x_train, y_train, x_valid, _, users_valid, dimension = _encode_train_validation(train, valid)
    model = TorchFM(dimension, k=config.k, lr=config.lr, seed=seed).to(device)
    rng = np.random.default_rng(seed)
    train_x = torch.from_numpy(x_train).to(device)
    train_y = torch.from_numpy(y_train).to(device)
    valid_x = torch.from_numpy(x_valid).to(device)
    best_primary, best_state, bad_epochs = -1.0, None, 0
    started = perf_counter()
    for _epoch in range(1, config.epochs + 1):
        indices = rng.permutation(len(y_train))
        for start in range(0, len(indices), config.batch_size):
            index = torch.from_numpy(indices[start : start + config.batch_size]).to(device)
            model.step(train_x[index], train_y[index])
        scores = model.predict(valid_x).cpu().numpy()
        metrics = adapter.evaluator.score_development(
            "valid", users_valid, [int(row.label) for row in valid], scores
        )
        if metrics["primary"] > best_primary + 1e-5:
            best_primary, bad_epochs = metrics["primary"], 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            bad_epochs += 1
            if bad_epochs >= config.patience:
                break
    if best_state is None:
        raise RuntimeError("PyTorch control did not produce a checkpoint")
    model.load_state_dict(best_state)
    scores = model.predict(valid_x).cpu().numpy()
    metrics = adapter.evaluator.score_development(
        "valid", users_valid, [int(row.label) for row in valid], scores
    )
    metrics["wall_seconds"] = perf_counter() - started
    metrics["seed"] = float(seed)
    return metrics

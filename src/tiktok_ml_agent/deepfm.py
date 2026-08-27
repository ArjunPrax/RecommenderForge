"""Compact DeepFM-style BPR backbone for a controlled architecture experiment."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from torch import nn
from torch.nn import functional as functional

from .baseline_runner import StarterFMConfig, _encode_train_validation
from .kuairand import KuaiRandPureAdapter
from .ranking_fm import _group_indices, _sample_bpr_pairs
from .temporal import temporal_primary_windows


class DeepFM(nn.Module):
    """FM interactions plus a small nonlinear field-embedding tower."""

    def __init__(self, dimension: int, field_count: int, k: int = 16, hidden: int = 64, lr: float = 0.001, seed: int = 0) -> None:
        super().__init__()
        generator = torch.Generator(device="cpu").manual_seed(seed)
        self.V = nn.Parameter(torch.randn((dimension, k), generator=generator) * 0.01)
        self.W = nn.Parameter(torch.zeros(dimension))
        self.b = nn.Parameter(torch.zeros(()))
        self.tower = nn.Sequential(nn.Linear(field_count * k, hidden), nn.ReLU(), nn.Linear(hidden, 1))
        self.optimizer = torch.optim.Adam(self.parameters(), lr=lr, weight_decay=1e-6)

    def logits(self, x: torch.Tensor) -> torch.Tensor:
        embeddings = self.V[x]
        summed = embeddings.sum(dim=1)
        interactions = 0.5 * ((summed**2).sum(dim=1) - (embeddings**2).sum(dim=(1, 2)))
        deep = self.tower(embeddings.flatten(start_dim=1)).squeeze(1)
        return self.b + self.W[x].sum(dim=1) + interactions + deep

    def step_loss(self, loss: torch.Tensor) -> None:
        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        self.optimizer.step()

    @torch.no_grad()
    def predict(self, x: torch.Tensor, batch_size: int = 200_000) -> torch.Tensor:
        return torch.cat([self.logits(x[start : start + batch_size]) for start in range(0, len(x), batch_size)])


@dataclass(frozen=True, slots=True)
class DeepFMConfig(StarterFMConfig):
    hidden: int = 64
    pair_batch_size: int = 8192


def run_deepfm_bpr(
    starter_kit_dir: str | Path, data_dir: str | Path, seed: int, config: DeepFMConfig | None = None,
    checkpoint_path: str | Path | None = None,
) -> dict[str, float | str]:
    config = config or DeepFMConfig()
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir)
    train, valid = adapter.development_rows("train"), adapter.development_rows("valid")
    x_train, y_train, x_valid, _, users_valid, dimension = _encode_train_validation(train, valid)
    model = DeepFM(dimension, x_train.shape[1], k=config.k, hidden=config.hidden, lr=config.lr, seed=seed)
    train_x, valid_x = torch.from_numpy(x_train), torch.from_numpy(x_valid)
    groups = _group_indices([row.user_id for row in train]); rng = np.random.default_rng(seed)
    best_primary, best_state, bad_epochs = -1.0, None, 0; started = perf_counter()
    for _epoch in range(config.epochs):
        positives, negatives = _sample_bpr_pairs(groups, y_train, rng); order = rng.permutation(len(positives))
        for start in range(0, len(order), config.pair_batch_size):
            chosen = order[start : start + config.pair_batch_size]
            pos, neg = torch.from_numpy(positives[chosen]), torch.from_numpy(negatives[chosen])
            model.step_loss(-functional.logsigmoid(model.logits(train_x[pos]) - model.logits(train_x[neg])).mean())
        scores = model.predict(valid_x).numpy()
        metrics = adapter.evaluator.score_development("valid", users_valid, [int(row.label) for row in valid], scores)
        if metrics["primary"] > best_primary + 1e-5:
            best_primary, bad_epochs = metrics["primary"], 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            bad_epochs += 1
            if bad_epochs >= config.patience: break
    if best_state is None: raise RuntimeError("DeepFM did not produce a checkpoint")
    model.load_state_dict(best_state); validation_scores = model.predict(valid_x).numpy()
    metrics = adapter.evaluator.score_development("valid", users_valid, [int(row.label) for row in valid], validation_scores)
    metrics.update(temporal_primary_windows(valid, validation_scores, lambda users, labels, values: adapter.evaluator.score_development("valid", users, labels, values)))
    if checkpoint_path is not None:
        checkpoint = Path(checkpoint_path); checkpoint.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"model_type": "deepfm", "state_dict": model.state_dict(), "seed": seed, "configuration": {"k": config.k, "hidden": config.hidden, "field_count": x_train.shape[1]}}, checkpoint)
        prediction = checkpoint.with_suffix(".validation.npy"); np.save(prediction, validation_scores)
        metrics.update({"checkpoint_path": str(checkpoint), "checkpoint_sha256": sha256(checkpoint.read_bytes()).hexdigest(), "validation_prediction_sha256": sha256(prediction.read_bytes()).hexdigest()})
    metrics.update({"wall_seconds": perf_counter() - started, "seed": float(seed)})
    return metrics

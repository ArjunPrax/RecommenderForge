"""Shared-FM multi-feedback candidate: BPR for long view plus auxiliary BCE."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from torch.nn import functional as functional

from .baseline_runner import StarterFMConfig, _encode_train_validation
from .kuairand import KuaiRandPureAdapter
from .ranking_fm import _group_indices, _sample_bpr_pairs
from .torch_fm import TorchFM
from .temporal import temporal_primary_windows


class MultiTaskFM(TorchFM):
    """One shared FM and small task-specific biases for observed feedback heads."""

    def __init__(self, *args: object, task_count: int, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.task_bias = torch.nn.Parameter(torch.zeros(task_count, dtype=torch.float32))

    def task_logits(self, x: torch.Tensor, task_index: int) -> torch.Tensor:
        return self.logits(x) + self.task_bias[task_index]

    def _step_extra_parameters(self) -> None:
        if self.task_bias.grad is None:
            raise RuntimeError("missing multi-task bias gradient")
        self.task_bias.add_(self.task_bias.grad, alpha=-self.lr)


@dataclass(frozen=True, slots=True)
class MultiTaskConfig(StarterFMConfig):
    auxiliary_weight: float = 0.15
    pair_batch_size: int = 8192
    auxiliary_batch_size: int = 8192

    def __post_init__(self) -> None:
        if not 0 < self.auxiliary_weight <= 1:
            raise ValueError("auxiliary_weight must be in (0, 1]")


def run_multitask_bpr(
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    seed: int,
    config: MultiTaskConfig | None = None,
    checkpoint_path: str | Path | None = None,
) -> dict[str, float | str]:
    """Train the primary BPR objective with train-only click/like/follow BCE."""
    config = config or MultiTaskConfig()
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir)
    train = adapter.development_rows("train", include_auxiliary_labels=True)
    valid = adapter.development_rows("valid")
    if any(row.auxiliary_labels is None for row in train):
        raise RuntimeError("training rows are missing auxiliary labels")
    x_train, y_train, x_valid, _, users_valid, dimension = _encode_train_validation(train, valid)
    aux_train = np.asarray([row.auxiliary_labels for row in train], dtype=np.float32)
    groups = _group_indices([row.user_id for row in train])
    model = MultiTaskFM(dimension, k=config.k, lr=config.lr, seed=seed, task_count=4)
    x_tensor = torch.from_numpy(x_train)
    y_tensor = torch.from_numpy(y_train)
    aux_tensor = torch.from_numpy(aux_train)
    valid_tensor = torch.from_numpy(x_valid)
    rng = np.random.default_rng(seed)
    best_primary, best_state, bad_epochs = -1.0, None, 0
    started = perf_counter()
    for _epoch in range(1, config.epochs + 1):
        positives, negatives = _sample_bpr_pairs(groups, y_train, rng)
        order = rng.permutation(len(positives))
        aux_order = rng.permutation(len(y_train))
        for batch_number, start in enumerate(range(0, len(order), config.pair_batch_size)):
            selected = order[start : start + config.pair_batch_size]
            pos = torch.from_numpy(positives[selected])
            neg = torch.from_numpy(negatives[selected])
            pair_loss = -functional.logsigmoid(model.task_logits(x_tensor[pos], 0) - model.task_logits(x_tensor[neg], 0)).mean()
            aux_start = (batch_number * config.auxiliary_batch_size) % len(aux_order)
            auxiliary_indices = aux_order[aux_start : aux_start + config.auxiliary_batch_size]
            if len(auxiliary_indices) == 0:
                auxiliary_indices = aux_order[: config.auxiliary_batch_size]
            auxiliary_index_tensor = torch.from_numpy(auxiliary_indices)
            auxiliary_loss = torch.stack(
                [
                    functional.binary_cross_entropy_with_logits(
                        model.task_logits(x_tensor[auxiliary_index_tensor], task + 1),
                        aux_tensor[auxiliary_index_tensor, task],
                    )
                    for task in range(3)
                ]
            ).mean()
            model.step_loss(pair_loss + config.auxiliary_weight * auxiliary_loss)
        scores = model.task_logits(valid_tensor, 0).detach().numpy()
        metrics = adapter.evaluator.score_development("valid", users_valid, [int(row.label) for row in valid], scores)
        if metrics["primary"] > best_primary + 1e-5:
            best_primary, bad_epochs = metrics["primary"], 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            bad_epochs += 1
            if bad_epochs >= config.patience:
                break
    if best_state is None:
        raise RuntimeError("multi-task BPR did not produce a checkpoint")
    model.load_state_dict(best_state)
    validation_scores = model.task_logits(valid_tensor, 0).detach().numpy()
    metrics = adapter.evaluator.score_development("valid", users_valid, [int(row.label) for row in valid], validation_scores)
    metrics.update(
        temporal_primary_windows(
            valid,
            validation_scores,
            lambda users, labels, values: adapter.evaluator.score_development("valid", users, labels, values),
        )
    )
    if checkpoint_path is not None:
        checkpoint = Path(checkpoint_path)
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "seed": seed, "configuration": config}, checkpoint)
        prediction_path = checkpoint.with_suffix(".validation.npy")
        np.save(prediction_path, validation_scores)
        metrics["checkpoint_path"] = str(checkpoint)
        metrics["checkpoint_sha256"] = sha256(checkpoint.read_bytes()).hexdigest()
        metrics["validation_prediction_sha256"] = sha256(prediction_path.read_bytes()).hexdigest()
    metrics.update({"wall_seconds": perf_counter() - started, "seed": float(seed)})
    return metrics

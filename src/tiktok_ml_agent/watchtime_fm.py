"""Train-only watch-completion auxiliary objective for the BPR FM.

``play_time_ms`` is a post-exposure outcome.  It is requested only for the
training split and is never present in validation or test row objects.  The
only evaluated score remains the primary long-view BPR head.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from torch.nn import functional as functional

from .baseline_runner import StarterFMConfig, _encode_train_validation
from .kuairand import KuaiRandPureAdapter, KuaiRandRow
from .ranking_fm import _group_indices, _sample_bpr_pairs
from .temporal import temporal_primary_windows
from .torch_fm import TorchFM


class WatchTimeFM(TorchFM):
    """Primary BPR scorer plus one bounded completion-prediction head."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.watch_bias = torch.nn.Parameter(torch.zeros((), dtype=torch.float32))

    def watch_logits(self, x: torch.Tensor) -> torch.Tensor:
        return self.logits(x) + self.watch_bias

    def _step_extra_parameters(self) -> None:
        if self.watch_bias.grad is None:
            raise RuntimeError("missing watch-time head gradient")
        self.watch_bias.add_(self.watch_bias.grad, alpha=-self.lr)


@dataclass(frozen=True, slots=True)
class WatchTimeConfig(StarterFMConfig):
    auxiliary_weight: float = 0.10
    pair_batch_size: int = 8192
    auxiliary_batch_size: int = 8192

    def __post_init__(self) -> None:
        if not 0 < self.auxiliary_weight <= 1:
            raise ValueError("auxiliary_weight must be in (0, 1]")


def completion_targets(rows: list[KuaiRandRow]) -> np.ndarray:
    """Clip observed play duration to a valid [0, 1] completion target."""
    values: list[float] = []
    for row in rows:
        if row.watch_time_ms is None:
            raise ValueError("watch-time candidate requires train-only play_time_ms outcomes")
        values.append(float(np.clip(row.watch_time_ms / max(row.duration_ms, 1.0), 0.0, 1.0)))
    return np.asarray(values, dtype=np.float32)


def run_watchtime_bpr(
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    seed: int,
    config: WatchTimeConfig | None = None,
    checkpoint_path: str | Path | None = None,
) -> dict[str, float | str]:
    """Evaluate BPR with a train-only watch-completion auxiliary objective."""
    config = config or WatchTimeConfig()
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir)
    train = adapter.development_rows("train", include_watch_targets=True)
    valid = adapter.development_rows("valid")
    x_train, y_train, x_valid, _, users_valid, dimension = _encode_train_validation(train, valid)
    targets = completion_targets(train)
    groups = _group_indices([row.user_id for row in train])
    model = WatchTimeFM(dimension, k=config.k, lr=config.lr, seed=seed)
    x_tensor = torch.from_numpy(x_train)
    valid_tensor = torch.from_numpy(x_valid)
    target_tensor = torch.from_numpy(targets)
    rng = np.random.default_rng(seed)
    best_primary, best_state, bad_epochs = -1.0, None, 0
    started = perf_counter()
    for _epoch in range(1, config.epochs + 1):
        positives, negatives = _sample_bpr_pairs(groups, y_train, rng)
        order = rng.permutation(len(positives))
        target_order = rng.permutation(len(y_train))
        for batch_number, start in enumerate(range(0, len(order), config.pair_batch_size)):
            selected = order[start : start + config.pair_batch_size]
            pos = torch.from_numpy(positives[selected])
            neg = torch.from_numpy(negatives[selected])
            pair_loss = -functional.logsigmoid(model.logits(x_tensor[pos]) - model.logits(x_tensor[neg])).mean()
            target_start = (batch_number * config.auxiliary_batch_size) % len(target_order)
            auxiliary_indices = target_order[target_start : target_start + config.auxiliary_batch_size]
            if len(auxiliary_indices) == 0:
                auxiliary_indices = target_order[: config.auxiliary_batch_size]
            auxiliary_index_tensor = torch.from_numpy(auxiliary_indices)
            watch_loss = functional.binary_cross_entropy_with_logits(
                model.watch_logits(x_tensor[auxiliary_index_tensor]), target_tensor[auxiliary_index_tensor]
            )
            model.step_loss(pair_loss + config.auxiliary_weight * watch_loss)
        scores = model.predict(valid_tensor).numpy()
        metrics = adapter.evaluator.score_development("valid", users_valid, [int(row.label) for row in valid], scores)
        if metrics["primary"] > best_primary + 1e-5:
            best_primary, bad_epochs = metrics["primary"], 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            bad_epochs += 1
            if bad_epochs >= config.patience:
                break
    if best_state is None:
        raise RuntimeError("watch-time BPR did not produce a checkpoint")
    model.load_state_dict(best_state)
    validation_scores = model.predict(valid_tensor).numpy()
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
        torch.save(
            {
                "model_type": "watchtime",
                "state_dict": model.state_dict(),
                "seed": seed,
                "configuration": {"k": config.k, "lr": config.lr, "epochs": config.epochs, "patience": config.patience, "auxiliary_weight": config.auxiliary_weight},
            },
            checkpoint,
        )
        prediction_path = checkpoint.with_suffix(".validation.npy")
        np.save(prediction_path, validation_scores)
        metrics["checkpoint_path"] = str(checkpoint)
        metrics["checkpoint_sha256"] = sha256(checkpoint.read_bytes()).hexdigest()
        metrics["validation_prediction_sha256"] = sha256(prediction_path.read_bytes()).hexdigest()
    metrics.update({"wall_seconds": perf_counter() - started, "seed": float(seed)})
    return metrics

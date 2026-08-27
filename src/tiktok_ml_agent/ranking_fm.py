"""Ranking-objective FM candidates for EXP-004.

Both objectives train only from permitted train rows and evaluate through the
organizer validation evaluator. BPR samples positive/negative impressions from
the same user. The exact-listwise objective processes complete per-user logged
impression lists without negative sampling.
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
from .kuairand import KuaiRandPureAdapter
from .torch_fm import TorchFM


@dataclass(frozen=True, slots=True)
class RankingFMConfig(StarterFMConfig):
    objective: str = "bpr"  # bpr | listwise
    pair_batch_size: int = 8192
    group_batch_rows: int = 8192

    def __post_init__(self) -> None:
        if self.objective not in {"bpr", "listwise"}:
            raise ValueError("objective must be bpr or listwise")


def _group_indices(users: list[str]) -> list[np.ndarray]:
    groups: dict[str, list[int]] = {}
    for index, user in enumerate(users):
        groups.setdefault(user, []).append(index)
    return [np.asarray(indices, dtype=np.int64) for indices in groups.values()]


def _sample_bpr_pairs(groups: list[np.ndarray], labels: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    positives: list[np.ndarray] = []
    negatives: list[np.ndarray] = []
    for group in groups:
        group_labels = labels[group]
        pos = group[group_labels == 1]
        neg = group[group_labels == 0]
        if len(pos) and len(neg):
            positives.append(pos)
            negatives.append(rng.choice(neg, size=len(pos), replace=True))
    if not positives:
        raise ValueError("BPR requires at least one user with positive and negative impressions")
    return np.concatenate(positives), np.concatenate(negatives)


def _group_batches(groups: list[np.ndarray], max_rows: int) -> list[np.ndarray]:
    batches: list[np.ndarray] = []
    current: list[np.ndarray] = []
    current_rows = 0
    for group in groups:
        if current and current_rows + len(group) > max_rows:
            batches.append(np.concatenate(current))
            current, current_rows = [], 0
        current.append(group)
        current_rows += len(group)
    if current:
        batches.append(np.concatenate(current))
    return batches


def _exact_listwise_loss(logits: torch.Tensor, labels: torch.Tensor, lengths: list[int]) -> torch.Tensor:
    """Mean per-user softmax loss over complete logged impression lists."""
    group_ids = torch.repeat_interleave(
        torch.arange(len(lengths), device=logits.device),
        torch.tensor(lengths, device=logits.device),
    )
    n_groups = len(lengths)
    maximum = torch.full((n_groups,), -torch.inf, device=logits.device)
    maximum.scatter_reduce_(0, group_ids, logits, reduce="amax", include_self=True)
    shifted = torch.exp(logits - maximum[group_ids])
    denominator = torch.zeros(n_groups, device=logits.device).scatter_add_(0, group_ids, shifted)
    logsumexp = maximum + denominator.log()
    positive_sum = torch.zeros(n_groups, device=logits.device).scatter_add_(0, group_ids, logits * labels)
    positive_count = torch.zeros(n_groups, device=logits.device).scatter_add_(0, group_ids, labels)
    eligible = positive_count > 0
    if not bool(eligible.any()):
        raise ValueError("listwise objective requires at least one positive per batch")
    return (logsumexp[eligible] - positive_sum[eligible] / positive_count[eligible]).mean()


def run_ranking_fm(
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    seed: int,
    config: RankingFMConfig,
    device: str = "cpu",
    checkpoint_path: str | Path | None = None,
) -> dict[str, float | str]:
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir)
    train = adapter.development_rows("train")
    valid = adapter.development_rows("valid")
    x_train, y_train, x_valid, _, users_valid, dimension = _encode_train_validation(train, valid)
    users_train = [row.user_id for row in train]
    groups = _group_indices(users_train)
    model = TorchFM(dimension, k=config.k, lr=config.lr, seed=seed).to(device)
    x_tensor = torch.from_numpy(x_train).to(device)
    y_tensor = torch.from_numpy(y_train).to(device)
    x_valid_tensor = torch.from_numpy(x_valid).to(device)
    rng = np.random.default_rng(seed)
    best_primary, best_state, bad_epochs = -1.0, None, 0
    started = perf_counter()
    for _epoch in range(1, config.epochs + 1):
        if config.objective == "bpr":
            positives, negatives = _sample_bpr_pairs(groups, y_train, rng)
            order = rng.permutation(len(positives))
            for start in range(0, len(order), config.pair_batch_size):
                selected = order[start : start + config.pair_batch_size]
                pos = torch.from_numpy(positives[selected]).to(device)
                neg = torch.from_numpy(negatives[selected]).to(device)
                loss = -functional.logsigmoid(model.logits(x_tensor[pos]) - model.logits(x_tensor[neg])).mean()
                model.step_loss(loss)
        else:
            for batch_indices in _group_batches(groups, config.group_batch_rows):
                batch_labels = y_tensor[torch.from_numpy(batch_indices).to(device)]
                # Each batch is a concatenation of complete groups. Reconstruct lengths from user IDs.
                batch_users = [users_train[index] for index in batch_indices]
                lengths: list[int] = []
                last_user: str | None = None
                for user in batch_users:
                    if user != last_user:
                        lengths.append(1)
                        last_user = user
                    else:
                        lengths[-1] += 1
                batch_x = x_tensor[torch.from_numpy(batch_indices).to(device)]
                loss = _exact_listwise_loss(model.logits(batch_x), batch_labels, lengths)
                model.step_loss(loss)
        scores = model.predict(x_valid_tensor).cpu().numpy()
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
        raise RuntimeError("ranking model did not produce a checkpoint")
    model.load_state_dict(best_state)
    validation_scores = model.predict(x_valid_tensor).cpu().numpy()
    metrics = adapter.evaluator.score_development(
        "valid", users_valid, [int(row.label) for row in valid], validation_scores
    )
    if checkpoint_path is not None:
        checkpoint = Path(checkpoint_path)
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": model.state_dict(),
                "seed": seed,
                "objective": config.objective,
                "configuration": {
                    "k": config.k,
                    "lr": config.lr,
                    "epochs": config.epochs,
                    "patience": config.patience,
                },
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

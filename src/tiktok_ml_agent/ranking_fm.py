"""Ranking-objective FM candidates for EXP-004.

All objectives train only from permitted train rows and evaluate through the
organizer validation evaluator. BPR samples positive/negative impressions from
the same user. Lambda-BPR adds a detached nDCG@5 swap-gain weight to the same
pair loss. The exact-listwise objective processes complete per-user logged
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
from .history import prior_long_view_buckets, prior_video_tab_buckets
from .kuairand import KuaiRandPureAdapter
from .torch_fm import TorchFM
from .temporal import temporal_primary_windows


@dataclass(frozen=True, slots=True)
class RankingFMConfig(StarterFMConfig):
    objective: str = "bpr"  # bpr | lambda_bpr | listwise
    pair_batch_size: int = 8192
    group_batch_rows: int = 8192
    history_cross: bool = False
    temporal_day_cross: bool = False
    item_tab_history_cross: bool = False
    negatives_per_positive: int = 1
    lambda_mix: float = 0.5

    def __post_init__(self) -> None:
        if self.objective not in {"bpr", "lambda_bpr", "listwise"}:
            raise ValueError("objective must be bpr or listwise")
        if self.negatives_per_positive < 1:
            raise ValueError("negatives_per_positive must be at least one")
        if not 0 <= self.lambda_mix <= 1:
            raise ValueError("lambda_mix must be in [0, 1]")


def _group_indices(users: list[str]) -> list[np.ndarray]:
    groups: dict[str, list[int]] = {}
    for index, user in enumerate(users):
        groups.setdefault(user, []).append(index)
    return [np.asarray(indices, dtype=np.int64) for indices in groups.values()]


def _sample_bpr_pairs(
    groups: list[np.ndarray], labels: np.ndarray, rng: np.random.Generator, *, negatives_per_positive: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    if negatives_per_positive < 1:
        raise ValueError("negatives_per_positive must be at least one")
    positives: list[np.ndarray] = []
    negatives: list[np.ndarray] = []
    for group in groups:
        group_labels = labels[group]
        pos = group[group_labels == 1]
        neg = group[group_labels == 0]
        if len(pos) and len(neg):
            positives.append(np.repeat(pos, negatives_per_positive))
            negatives.append(rng.choice(neg, size=len(pos) * negatives_per_positive, replace=True))
    if not positives:
        raise ValueError("BPR requires at least one user with positive and negative impressions")
    return np.concatenate(positives), np.concatenate(negatives)


def _lambda_ndcg5_weights(
    groups: list[np.ndarray], labels: np.ndarray, scores: np.ndarray, positives: np.ndarray, negatives: np.ndarray,
) -> np.ndarray:
    """Detached per-pair nDCG@5 swap gains for same-user BPR pairs.

    The rankings used for the weights are deliberately detached from autograd;
    gradients still flow only through the pairwise score difference.  A weight
    is non-zero precisely when exchanging the sampled positive and negative
    can alter the user's top-five discounted gain.
    """
    ranks = np.empty(len(labels), dtype=np.int64)
    ideal_dcg: dict[int, float] = {}
    group_of = np.empty(len(labels), dtype=np.int64)
    for group_index, group in enumerate(groups):
        ordered = group[np.argsort(-scores[group], kind="stable")]
        ranks[ordered] = np.arange(len(group), dtype=np.int64)
        group_of[group] = group_index
        positive_count = int(labels[group].sum())
        ideal_dcg[group_index] = sum(1 / np.log2(rank + 2) for rank in range(min(5, positive_count)))
    weights = np.zeros(len(positives), dtype=np.float32)
    for index, (positive, negative) in enumerate(zip(positives, negatives)):
        if group_of[positive] != group_of[negative]:
            raise ValueError("Lambda-BPR pairs must remain within one user group")
        denominator = ideal_dcg[int(group_of[positive])]
        if denominator == 0:
            continue
        positive_discount = 1 / np.log2(ranks[positive] + 2) if ranks[positive] < 5 else 0.0
        negative_discount = 1 / np.log2(ranks[negative] + 2) if ranks[negative] < 5 else 0.0
        weights[index] = abs(positive_discount - negative_discount) / denominator
    return weights


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
    if sum((config.history_cross, config.temporal_day_cross, config.item_tab_history_cross)) > 1:
        raise ValueError("history, temporal-day, and video-tab feature candidates must be evaluated independently")
    if config.history_cross:
        train_history, valid_history = prior_long_view_buckets(train, valid)
        x_train, y_train, x_valid, _, users_valid, dimension = _encode_train_validation(
            train, valid, extra_train=train_history, extra_valid=valid_history
        )
    elif config.item_tab_history_cross:
        train_history, valid_history = prior_video_tab_buckets(train, valid)
        x_train, y_train, x_valid, _, users_valid, dimension = _encode_train_validation(
            train, valid, extra_train=train_history, extra_valid=valid_history
        )
    elif config.temporal_day_cross:
        # KuaiRand-Pure is confined to April/May 2022; date modulo seven is a
        # deterministic day-of-week proxy that is known at inference time.
        train_day = [f"weekday_{(row.date % 100 - 1) % 7}" for row in train]
        valid_day = [f"weekday_{(row.date % 100 - 1) % 7}" for row in valid]
        x_train, y_train, x_valid, _, users_valid, dimension = _encode_train_validation(
            train, valid, extra_train=train_day, extra_valid=valid_day
        )
    else:
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
        if config.objective in {"bpr", "lambda_bpr"}:
            positives, negatives = _sample_bpr_pairs(
                groups, y_train, rng, negatives_per_positive=config.negatives_per_positive,
            )
            lambda_weights = (
                _lambda_ndcg5_weights(groups, y_train, model.predict(x_tensor).detach().cpu().numpy(), positives, negatives)
                if config.objective == "lambda_bpr" else None
            )
            order = rng.permutation(len(positives))
            for start in range(0, len(order), config.pair_batch_size):
                selected = order[start : start + config.pair_batch_size]
                pos = torch.from_numpy(positives[selected]).to(device)
                neg = torch.from_numpy(negatives[selected]).to(device)
                pair_losses = -functional.logsigmoid(model.logits(x_tensor[pos]) - model.logits(x_tensor[neg]))
                if lambda_weights is None:
                    loss = pair_losses.mean()
                else:
                    raw_weights = torch.from_numpy(lambda_weights[selected]).to(device)
                    if bool((raw_weights > 0).any()):
                        normalized = raw_weights / raw_weights[raw_weights > 0].mean()
                        weighted_loss = (pair_losses * normalized).sum() / normalized.sum()
                        loss = (1 - config.lambda_mix) * pair_losses.mean() + config.lambda_mix * weighted_loss
                    else:
                        loss = pair_losses.mean()
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
                "state_dict": model.state_dict(),
                "seed": seed,
                "objective": config.objective,
                "history_cross": config.history_cross,
                "temporal_day_cross": config.temporal_day_cross,
                "item_tab_history_cross": config.item_tab_history_cross,
                "negatives_per_positive": config.negatives_per_positive,
                "lambda_mix": config.lambda_mix,
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

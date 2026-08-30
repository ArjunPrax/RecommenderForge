"""Leakage-safe user-history features for candidate-item FM crosses."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .kuairand import KuaiRandRow


@dataclass(frozen=True, slots=True)
class HistoryFeatureConfig:
    count_cap: int = 32
    rate_bins: int = 8


def _bucket(positive: int, total: int, config: HistoryFeatureConfig) -> str:
    count = min(total, config.count_cap)
    rate = 0 if total == 0 else min(config.rate_bins - 1, int((positive / total) * config.rate_bins))
    return f"hist_count_{count}_rate_{rate}"


def prior_long_view_buckets(
    train: list[KuaiRandRow], valid: list[KuaiRandRow], config: HistoryFeatureConfig | None = None
) -> tuple[list[str], list[str]]:
    """Return strict-prior train buckets and train-only frozen validation buckets.

    Training rows are ordered by observed event time. A row receives its feature
    before its own label updates state, preventing target leakage. Validation
    buckets are based on the completed training period only: no validation
    label, including an earlier validation event, enters an evaluation feature.
    """
    config = config or HistoryFeatureConfig()
    if any(row.label is None for row in train):
        raise ValueError("history construction requires permitted train labels")
    state: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    train_buckets = [""] * len(train)
    for index in sorted(range(len(train)), key=lambda item: (train[item].timestamp_ms, item)):
        row = train[index]
        positive, total = state[row.user_id]
        train_buckets[index] = _bucket(positive, total, config)
        state[row.user_id][0] += int(row.label or 0)
        state[row.user_id][1] += 1
    valid_buckets = [_bucket(*state[row.user_id], config) for row in valid]
    return train_buckets, valid_buckets


def prior_video_tab_buckets(
    train: list[KuaiRandRow], valid: list[KuaiRandRow], config: HistoryFeatureConfig | None = None
) -> tuple[list[str], list[str]]:
    """Return strict-prior global video×tab buckets and frozen evaluation buckets.

    Unlike a user-only feature, this is candidate-specific: impressions of
    different videos or tabs can receive different fields within one user's
    ranking list.  Training state is updated only after each observed event;
    evaluation uses the completed training state and never reads evaluation
    labels.  The caller may therefore pass label-less submission rows safely.
    """
    config = config or HistoryFeatureConfig()
    if any(row.label is None for row in train):
        raise ValueError("history construction requires permitted train labels")
    state: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    train_buckets = [""] * len(train)
    for index in sorted(range(len(train)), key=lambda item: (train[item].timestamp_ms, item)):
        row = train[index]
        key = (row.video_id, row.tab)
        positive, total = state[key]
        train_buckets[index] = _bucket(positive, total, config)
        state[key][0] += int(row.label or 0)
        state[key][1] += 1
    valid_buckets = [_bucket(*state[(row.video_id, row.tab)], config) for row in valid]
    return train_buckets, valid_buckets


def prior_user_author_buckets(
    train: list[KuaiRandRow], valid: list[KuaiRandRow], config: HistoryFeatureConfig | None = None
) -> tuple[list[str], list[str]]:
    """Return strict-prior user×author buckets and frozen evaluation buckets.

    This is a personalised candidate feature: within one user's impression
    list, videos from different authors can receive different fields.  As with
    every history feature, a training row is encoded before its own label
    updates the `(user_id, author_id)` state; validation and submission rows
    use the completed training state and never require their labels.
    """
    config = config or HistoryFeatureConfig()
    if any(row.label is None for row in train):
        raise ValueError("history construction requires permitted train labels")
    state: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    train_buckets = [""] * len(train)
    for index in sorted(range(len(train)), key=lambda item: (train[item].timestamp_ms, item)):
        row = train[index]
        key = (row.user_id, row.author_id)
        positive, total = state[key]
        train_buckets[index] = _bucket(positive, total, config)
        state[key][0] += int(row.label or 0)
        state[key][1] += 1
    valid_buckets = [_bucket(*state[(row.user_id, row.author_id)], config) for row in valid]
    return train_buckets, valid_buckets

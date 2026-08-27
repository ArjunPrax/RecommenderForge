"""Mechanism audit for candidate features under within-user ranking metrics."""

from __future__ import annotations

import numpy as np


def within_user_ordering_change(
    users: list[str], parent_scores: np.ndarray, candidate_scores: np.ndarray
) -> dict[str, int]:
    """Count whether a candidate actually changes any within-user ordering.

    A user-constant feature may alter calibrated scores but cannot improve a
    per-user rank. This audit catches that dead-end before a feature family is
    promoted as a research direction.
    """
    if len(users) != len(parent_scores) or len(users) != len(candidate_scores):
        raise ValueError("users and score vectors must have equal lengths")
    groups: dict[str, list[int]] = {}
    for index, user in enumerate(users):
        groups.setdefault(user, []).append(index)
    eligible_users = changed_users = changed_pairwise_relations = 0
    for indices in groups.values():
        if len(indices) < 2:
            continue
        eligible_users += 1
        base = parent_scores[indices]
        candidate = candidate_scores[indices]
        changed = False
        for left in range(len(indices)):
            for right in range(left + 1, len(indices)):
                parent_relation = np.sign(base[left] - base[right])
                candidate_relation = np.sign(candidate[left] - candidate[right])
                if parent_relation != candidate_relation:
                    changed_pairwise_relations += 1
                    changed = True
        changed_users += int(changed)
    return {
        "eligible_users": eligible_users,
        "changed_users": changed_users,
        "changed_pairwise_relations": changed_pairwise_relations,
    }

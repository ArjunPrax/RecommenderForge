"""Persistent cross-batch convergence accounting for autonomous research campaigns."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class CampaignIteration:
    batch_id: str
    run_ids: tuple[str, ...]
    primary: float
    selected_run_id: str


@dataclass(frozen=True, slots=True)
class CampaignStatus:
    baseline_primary: float
    significant_anchor: float
    best_primary: float
    best_run_id: str | None
    stagnation: int
    converged: bool
    iterations: tuple[CampaignIteration, ...]


class CampaignConvergence:
    """Epsilon/N logic over batches, rather than over sibling candidates."""

    def __init__(self, baseline_primary: float, epsilon: float, patience: int) -> None:
        self.baseline_primary, self.epsilon, self.patience = baseline_primary, epsilon, patience
        self.iterations: list[CampaignIteration] = []

    def add_batch(self, batch_id: str, records: Iterable[tuple[str, float]]) -> CampaignStatus:
        values = list(records)
        if not values:
            raise ValueError("campaign batches require at least one successful scored run")
        selected_run_id, primary = max(values, key=lambda item: item[1])
        self.iterations.append(CampaignIteration(batch_id, tuple(run_id for run_id, _ in values), primary, selected_run_id))
        return self.status()

    def status(self) -> CampaignStatus:
        anchor, stagnation = self.baseline_primary, 0
        best_primary, best_run_id = self.baseline_primary, None
        for iteration in self.iterations:
            if iteration.primary > best_primary:
                best_primary, best_run_id = iteration.primary, iteration.selected_run_id
            if iteration.primary > anchor + self.epsilon:
                anchor, stagnation = iteration.primary, 0
            else:
                stagnation += 1
        return CampaignStatus(self.baseline_primary, anchor, best_primary, best_run_id, stagnation, stagnation >= self.patience, tuple(self.iterations))

    def write(self, path: str | Path) -> Path:
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        status = self.status()
        payload = asdict(status)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

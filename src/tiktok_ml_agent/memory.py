"""Retrieval and bounded working-memory snapshots for research planning."""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from .contracts import EvidenceCard
from .ledger import ExperimentLedger


TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


@dataclass(frozen=True, slots=True)
class MemoryPolicy:
    max_evidence_cards: int = 6
    consolidation_interval: int = 5
    prompt_token_cap: int = 12_000


class KnowledgeBase:
    def __init__(self, cards: Iterable[EvidenceCard]) -> None:
        self.cards = {card.evidence_id: card for card in cards}

    def retrieve(self, query: str, limit: int = 6) -> list[EvidenceCard]:
        query_tokens = _tokens(query)
        ranked: list[tuple[int, str, EvidenceCard]] = []
        for card in self.cards.values():
            haystack = " ".join((card.title, card.claim, card.applicability, *card.assumptions, *card.risks))
            overlap = len(query_tokens & _tokens(haystack))
            if overlap:
                ranked.append((overlap, card.evidence_id, card))
        return [card for _, _, card in sorted(ranked, key=lambda item: (-item[0], item[1]))[:limit]]


class MemoryManager:
    def __init__(self, ledger: ExperimentLedger, policy: MemoryPolicy | None = None) -> None:
        self.ledger = ledger
        self.policy = policy or MemoryPolicy()

    def should_consolidate(self, projected_prompt_tokens: int) -> bool:
        run_count = len(self.ledger.list_runs())
        return (
            run_count > 0 and run_count % self.policy.consolidation_interval == 0
        ) or projected_prompt_tokens > self.policy.prompt_token_cap

    def consolidate(self) -> dict[str, object]:
        runs = self.ledger.list_runs()
        succeeded = [run for run in runs if run["status"] == "succeeded"]
        rejected = [run for run in runs if run["status"] in {"rejected", "failed", "recovered"}]
        ranked = sorted(succeeded, key=lambda run: run.get("metrics", {}).get("primary", float("-inf")), reverse=True)
        payload: dict[str, object] = {
            "best_runs": [
                {
                    "run_id": run["run_id"],
                    "experiment_id": run["experiment_id"],
                    "primary": run.get("metrics", {}).get("primary"),
                    "operator_family": run["operator_family"],
                }
                for run in ranked[:3]
            ],
            "negative_findings": [
                {
                    "run_id": run["run_id"],
                    "experiment_id": run["experiment_id"],
                    "operator_family": run["operator_family"],
                    "error": run.get("error"),
                    "diagnosis": run.get("diagnosis", {}).get("summary"),
                }
                for run in rejected[-10:]
            ],
            "source_run_ids": [run["run_id"] for run in runs],
            "unresolved_questions": [],
        }
        snapshot_hash = sha256(repr(payload).encode()).hexdigest()
        self.ledger.save_memory_snapshot(snapshot_hash, len(runs), payload)
        return {"snapshot_id": snapshot_hash, "source_run_count": len(runs), "payload": payload}

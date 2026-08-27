"""Bounded, schema-validated planning for autonomous research batches.

The controller never executes raw model prose.  A provider must return the
small JSON shape below; this module turns it into immutable experiment specs,
then the controller applies parent/checkpoint and budget rules.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.request import Request, urlopen

from .contracts import EvidenceCard, ExperimentSpec, OperatorFamily, RunClass
from .controller import CandidateBatch
from .memory import KnowledgeBase


class PlannerError(ValueError):
    """A provider response was malformed or violated the research contract."""


@dataclass(frozen=True, slots=True)
class PlannerContext:
    goal: str
    experiment_ids: tuple[str, ...]
    run_class: RunClass
    parent_run_id: str | None
    parent_checkpoint_sha256: str | None
    allowed_operator_families: tuple[OperatorFamily, ...]
    allowed_paths: tuple[str, ...]
    token_budget: int
    compute_budget_seconds: int


@dataclass(frozen=True, slots=True)
class PlannerResult:
    batch: CandidateBatch
    rationale: str
    input_tokens: int = 0
    output_tokens: int = 0
    provider_response_id: str | None = None


class Planner(Protocol):
    def plan(self, context: PlannerContext, knowledge: KnowledgeBase) -> PlannerResult: ...


def _schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["rationale", "candidates"],
        "properties": {
            "rationale": {"type": "string", "minLength": 1},
            "candidates": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "experiment_id",
                        "operator_family",
                        "hypothesis",
                        "expected_mechanism",
                        "evidence_ids",
                        "configuration",
                        "controlled_variables",
                    ],
                    "properties": {
                        "experiment_id": {"type": "string"},
                        "operator_family": {"type": "string"},
                        "hypothesis": {"type": "string", "minLength": 1},
                        "expected_mechanism": {"type": "string", "minLength": 1},
                        "evidence_ids": {"type": "array", "items": {"type": "string"}},
                        "configuration": {"type": "object"},
                        "controlled_variables": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        },
    }


def _build_result(
    raw: dict[str, Any], context: PlannerContext, cards: dict[str, EvidenceCard], *, input_tokens: int = 0,
    output_tokens: int = 0, provider_response_id: str | None = None,
) -> PlannerResult:
    if not isinstance(raw, dict) or not isinstance(raw.get("rationale"), str):
        raise PlannerError("planner result requires a rationale")
    candidates_raw = raw.get("candidates")
    if not isinstance(candidates_raw, list) or not 1 <= len(candidates_raw) <= 3:
        raise PlannerError("planner must propose one to three candidates")
    candidates: list[ExperimentSpec] = []
    used_ids: set[str] = set()
    for proposal in candidates_raw:
        if not isinstance(proposal, dict):
            raise PlannerError("candidate must be an object")
        experiment_id = proposal.get("experiment_id")
        if experiment_id not in context.experiment_ids or experiment_id in used_ids:
            raise PlannerError("candidate used an unknown or repeated stable experiment ID")
        used_ids.add(experiment_id)
        try:
            family = OperatorFamily(proposal.get("operator_family"))
        except ValueError as exc:
            raise PlannerError("candidate uses an unknown operator family") from exc
        if family not in context.allowed_operator_families:
            raise PlannerError(f"operator family {family} is not approved for this batch")
        evidence_ids = tuple(proposal.get("evidence_ids", ()))
        if any(evidence_id not in cards for evidence_id in evidence_ids):
            raise PlannerError("candidate cites evidence that is not in the provided knowledge base")
        candidates.append(
            ExperimentSpec(
                experiment_id=experiment_id,
                run_class=context.run_class,
                operator_family=family,
                hypothesis=str(proposal.get("hypothesis", "")),
                expected_mechanism=str(proposal.get("expected_mechanism", "")),
                parent_run_id=context.parent_run_id,
                parent_checkpoint_sha256=context.parent_checkpoint_sha256,
                evidence_ids=evidence_ids,
                configuration=dict(proposal.get("configuration", {})),
                controlled_variables=tuple(proposal.get("controlled_variables", ())),
                allowed_paths=context.allowed_paths,
                token_budget=context.token_budget,
                compute_budget_seconds=context.compute_budget_seconds,
            )
        )
    return PlannerResult(
        batch=CandidateBatch(
            batch_id=f"planner-{context.experiment_ids[0].lower()}",
            parent_run_id=context.parent_run_id,
            parent_checkpoint_sha256=context.parent_checkpoint_sha256,
            candidates=tuple(candidates),
        ),
        rationale=raw["rationale"],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        provider_response_id=provider_response_id,
    )


class FixedPlanner:
    """A deterministic planner used for qualification and offline reproducibility."""

    def __init__(self, proposal: dict[str, Any]) -> None:
        self.proposal = proposal

    def plan(self, context: PlannerContext, knowledge: KnowledgeBase) -> PlannerResult:
        return _build_result(self.proposal, context, knowledge.cards)


class OpenAIResponsesPlanner:
    """Optional Responses-API planner; no API key or network call is needed to run locally.

    The model is deliberately restricted to planning JSON. It receives retrieved
    evidence and ledger summaries, never data rows, labels, secrets, or a shell.
    """

    endpoint = "https://api.openai.com/v1/responses"

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise PlannerError("OPENAI_API_KEY is required only for the optional OpenAI planner")

    def plan(self, context: PlannerContext, knowledge: KnowledgeBase) -> PlannerResult:
        cards = knowledge.retrieve(context.goal, limit=6)
        prompt = {
            "goal": context.goal,
            "approved_experiment_ids": context.experiment_ids,
            "run_class": str(context.run_class),
            "parent_run_id": context.parent_run_id,
            "approved_operator_families": [str(family) for family in context.allowed_operator_families],
            "budgets": {"llm_output_tokens": context.token_budget, "compute_seconds": context.compute_budget_seconds},
            "invariants": [
                "Propose only one to three siblings from the same immutable parent.",
                "Do not request test labels, test scores, external training data, shell commands, or code patches.",
                "State a falsifiable hypothesis and expected mechanism for every candidate.",
            ],
            "evidence": [card.to_dict() for card in cards],
        }
        payload = {
            "model": self.model,
            "input": json.dumps(prompt, sort_keys=True),
            "max_output_tokens": context.token_budget,
            "store": False,
            "text": {"format": {"type": "json_schema", "name": "research_batch", "strict": True, "schema": _schema()}},
        }
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=60) as response:  # nosec B310 - fixed HTTPS endpoint
            reply = json.loads(response.read().decode())
        output = reply.get("output_text")
        if not output:
            pieces = [part.get("text", "") for item in reply.get("output", []) for part in item.get("content", [])]
            output = "".join(pieces)
        try:
            raw = json.loads(output)
        except (TypeError, json.JSONDecodeError) as exc:
            raise PlannerError("planner response did not contain valid JSON") from exc
        usage = reply.get("usage", {})
        return _build_result(
            raw,
            context,
            knowledge.cards,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            provider_response_id=reply.get("id"),
        )

"""Persistent cross-batch convergence accounting for autonomous research campaigns."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .ledger import ExperimentLedger


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


class CampaignEvidenceError(ValueError):
    """Raised when a declared research campaign cannot be evidenced safely."""


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise CampaignEvidenceError(f"campaign field {field!r} must be a non-empty string")
    return value


def _load_campaign(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CampaignEvidenceError(f"cannot read campaign configuration: {error}") from error
    if not isinstance(payload, dict):
        raise CampaignEvidenceError("campaign configuration must be a JSON object")
    for field in ("campaign_id", "benchmark_id"):
        _required_string(payload, field)
    if not isinstance(payload.get("baseline_primary"), (int, float)):
        raise CampaignEvidenceError("campaign baseline_primary must be numeric")
    if not isinstance(payload.get("batches"), list) or not payload["batches"]:
        raise CampaignEvidenceError("campaign must declare at least one batch")
    payload["_base_dir"] = config_path.parent
    return payload


def evaluate_campaign(path: str | Path) -> dict[str, Any]:
    """Materialize a cross-ledger convergence report from explicit run references.

    The JSON configuration is intentionally declarative rather than discovering
    every ledger in ``artifacts/``.  This prevents failed, superseded, or
    unrelated research runs from silently becoming convergence evidence.
    """
    config = _load_campaign(path)
    epsilon = float(config.get("epsilon", 0.002))
    patience = int(config.get("patience", 3))
    tracker = CampaignConvergence(float(config["baseline_primary"]), epsilon, patience)
    seen_run_refs: set[tuple[str, str]] = set()
    seen_batch_ids: set[str] = set()
    resource_totals: dict[str, float] = {}
    evaluator_hashes: set[str] = set()
    resolved_batches: list[dict[str, Any]] = []
    for ordinal, raw_batch in enumerate(config["batches"], start=1):
        if not isinstance(raw_batch, dict):
            raise CampaignEvidenceError(f"batch {ordinal} must be an object")
        batch_id = _required_string(raw_batch, "batch_id")
        if batch_id in seen_batch_ids:
            raise CampaignEvidenceError(f"duplicate batch_id: {batch_id}")
        seen_batch_ids.add(batch_id)
        raw_runs = raw_batch.get("runs")
        if not isinstance(raw_runs, list) or not raw_runs:
            raise CampaignEvidenceError(f"batch {batch_id} must contain at least one run")
        scored_runs: list[tuple[str, float]] = []
        evidence_runs: list[dict[str, Any]] = []
        for raw_ref in raw_runs:
            if not isinstance(raw_ref, dict):
                raise CampaignEvidenceError(f"batch {batch_id} contains an invalid run reference")
            relative_ledger = _required_string(raw_ref, "ledger")
            run_id = _required_string(raw_ref, "run_id")
            ledger_path = (config["_base_dir"] / relative_ledger).resolve()
            if not ledger_path.is_file():
                raise CampaignEvidenceError(f"ledger does not exist: {ledger_path}")
            ref = (str(ledger_path), run_id)
            if ref in seen_run_refs:
                raise CampaignEvidenceError(f"run referenced more than once: {run_id}")
            seen_run_refs.add(ref)
            ledger = ExperimentLedger(ledger_path)
            try:
                run = ledger.get_run(run_id)
            finally:
                ledger.close()
            if run["status"] != "succeeded":
                raise CampaignEvidenceError(f"run {run_id} is not succeeded")
            if run["run_class"] not in {"research", "designated_final"}:
                raise CampaignEvidenceError(f"run {run_id} has ineligible class {run['run_class']}")
            if run["benchmark_id"] != config["benchmark_id"]:
                raise CampaignEvidenceError(f"run {run_id} belongs to {run['benchmark_id']}, not {config['benchmark_id']}")
            if "primary" not in run.get("metrics", {}):
                raise CampaignEvidenceError(f"run {run_id} has no primary metric")
            evaluator_hash = run.get("evaluator_sha256")
            if not isinstance(evaluator_hash, str) or not evaluator_hash:
                raise CampaignEvidenceError(f"run {run_id} has no evaluator hash")
            evaluator_hashes.add(evaluator_hash)
            primary = float(run["metrics"]["primary"])
            scored_runs.append((run_id, primary))
            evidence_runs.append({
                "ledger": str(ledger_path), "run_id": run_id, "experiment_id": run["experiment_id"],
                "primary": primary, "parent_run_id": run.get("parent_run_id"),
                "checkpoint_manifest": run.get("checkpoint_manifest"),
            })
            for name, value in run.get("resource_usage", {}).items():
                resource_totals[name] = resource_totals.get(name, 0.0) + float(value)
        status = tracker.add_batch(batch_id, scored_runs)
        if status.converged and ordinal != len(config["batches"]):
            raise CampaignEvidenceError("campaign declares additional batches after convergence")
        resolved_batches.append({"batch_id": batch_id, "runs": evidence_runs, "selected_run_id": status.iterations[-1].selected_run_id, "selected_primary": status.iterations[-1].primary})
    if len(evaluator_hashes) != 1:
        raise CampaignEvidenceError("campaign mixes evaluator identities")
    status = tracker.status()
    best_run: dict[str, Any] | None = None
    if status.best_run_id is not None:
        for batch in resolved_batches:
            best_run = next((run for run in batch["runs"] if run["run_id"] == status.best_run_id), None)
            if best_run is not None:
                break
    return {
        "campaign_id": config["campaign_id"], "benchmark_id": config["benchmark_id"],
        "baseline_primary": status.baseline_primary, "epsilon": epsilon, "patience": patience,
        "converged": status.converged, "stagnation": status.stagnation,
        "significant_anchor": status.significant_anchor, "best_primary": status.best_primary,
        "best_run_id": status.best_run_id, "evaluator_sha256": next(iter(evaluator_hashes)),
        "best_run": best_run, "resource_totals": resource_totals, "batches": resolved_batches,
    }


def write_campaign_report(campaign_path: str | Path, output_path: str | Path) -> Path:
    """Write an auditable, machine-readable campaign status without mutating runs."""
    report = evaluate_campaign(campaign_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return output

"""Bind a converged campaign's best frozen checkpoint as a designated final."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from .campaign import CampaignEvidenceError
from .contracts import OperatorFamily, RunClass, RunRecord, RunStatus, hash_file
from .ledger import ExperimentLedger


def designate_final(*, campaign_report_path: str | Path, final_ledger_path: str | Path) -> dict[str, str]:
    """Create one immutable designated-final record from campaign evidence.

    This operation neither retrains nor scores the test split.  It copies only
    the selected source record's already-measured validation provenance and
    records the campaign-report hash that authorized the designation.
    """
    campaign_path = Path(campaign_report_path)
    try:
        campaign: dict[str, Any] = json.loads(campaign_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CampaignEvidenceError(f"cannot read campaign report: {error}") from error
    if campaign.get("converged") is not True:
        raise CampaignEvidenceError("cannot designate a final from an unconverged campaign")
    source_ref = campaign.get("best_run")
    if not isinstance(source_ref, dict):
        raise CampaignEvidenceError("converged campaign has no eligible best run")
    source_ledger_path = Path(str(source_ref.get("ledger", "")))
    source_run_id = source_ref.get("run_id")
    if not source_ledger_path.is_file() or not isinstance(source_run_id, str):
        raise CampaignEvidenceError("campaign best-run reference is unavailable")
    source_ledger = ExperimentLedger(source_ledger_path)
    try:
        source = source_ledger.get_run(source_run_id)
    finally:
        source_ledger.close()
    if source["status"] != "succeeded" or source["run_class"] not in {"research", "designated_final"}:
        raise CampaignEvidenceError("campaign best source is not an eligible completed run")
    if source.get("evaluator_sha256") != campaign.get("evaluator_sha256"):
        raise CampaignEvidenceError("campaign and source evaluator identities differ")
    manifest = source.get("checkpoint_manifest")
    if not isinstance(manifest, dict):
        raise CampaignEvidenceError("campaign best source has no frozen checkpoint manifest")
    checkpoint = Path(str(manifest.get("checkpoint_path", "")))
    if not checkpoint.is_file() or hash_file(checkpoint) != manifest.get("checkpoint_sha256"):
        raise CampaignEvidenceError("campaign best checkpoint is unavailable or changed")
    campaign_hash = hash_file(campaign_path)
    final_id = f"final-{sha256((campaign_hash + source_run_id).encode()).hexdigest()[:12]}"
    ledger = ExperimentLedger(final_ledger_path)
    try:
        record = RunRecord(
            run_id=final_id,
            experiment_id=str(source["experiment_id"]),
            run_class=RunClass.DESIGNATED_FINAL,
            status=RunStatus.RUNNING,
            benchmark_id=str(source["benchmark_id"]),
            operator_family=OperatorFamily(str(source["operator_family"])),
            hypothesis="Designate the converged campaign's frozen validation-best checkpoint without retraining.",
            parent_run_id=source_run_id,
            code_revision=source.get("code_revision"),
            diff_sha256=source.get("diff_sha256"),
            data_fingerprint=source.get("data_fingerprint"),
            evaluator_sha256=source.get("evaluator_sha256"),
            configuration_sha256=source.get("configuration_sha256"),
            seeds=list(source.get("seeds", [])),
            metrics={str(key): float(value) for key, value in source.get("metrics", {}).items()},
            checkpoint_manifest=manifest,
            diagnosis={
                "summary": "Designated final reuses the converged campaign's immutable source checkpoint.",
                "campaign_report_path": str(campaign_path),
                "campaign_report_sha256": campaign_hash,
                "source_ledger": str(source_ledger_path),
                "source_run_id": source_run_id,
                "campaign_resource_totals": campaign.get("resource_totals", {}),
            },
            resource_usage={"designation_cpu_seconds": 0.0},
            interventions=0,
        )
        ledger.create_run(record)
        ledger.append_event(final_id, "designated_final_bound", {
            "campaign_report_sha256": campaign_hash, "source_ledger": str(source_ledger_path), "source_run_id": source_run_id,
        })
        record.status = RunStatus.SUCCEEDED
        ledger.finalize_run(record)
    finally:
        ledger.close()
    return {"final_ledger": str(Path(final_ledger_path)), "final_run_id": final_id, "source_run_id": source_run_id}

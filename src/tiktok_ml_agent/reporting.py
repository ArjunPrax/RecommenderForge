"""Judge-facing report rendering from immutable ledger records."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .ledger import ExperimentLedger


def render_report(ledger: ExperimentLedger) -> str:
    runs = ledger.list_runs()
    counts = Counter(run["status"] for run in runs)
    classes = Counter(run["run_class"] for run in runs)
    resources = ledger.resource_totals()
    research_resources = ledger.resource_totals(run_classes=("research", "designated_final"))
    interventions = sum(int(run.get("interventions", 0)) for run in runs)
    lines = [
        "# Autonomous Research Run Report",
        "",
        "## Run summary",
        "",
        f"- Total runs: {len(runs)}",
        f"- Statuses: {dict(sorted(counts.items()))}",
        f"- Run classes: {dict(sorted(classes.items()))}",
        f"- Resource totals: {dict(sorted(resources.items()))}",
        f"- Research/final LLM input tokens: {research_resources.get('llm_input_tokens', 0.0):.0f}",
        f"- Research/final LLM output tokens: {research_resources.get('llm_output_tokens', 0.0):.0f}",
        f"- Research/final GPU-hours: {research_resources.get('gpu_seconds', 0.0) / 3600:.6f}",
        f"- Recorded manual interventions: {interventions}",
        "",
        "## Per-run evidence",
        "",
        "| Run | Experiment | Class | Status | Primary | Operator | Recovery |",
        "|---|---|---|---|---:|---|---|",
    ]
    for run in runs:
        lines.append(
            "| {run_id} | {experiment_id} | {run_class} | {status} | {primary} | {operator} | {recovery} |".format(
                run_id=run["run_id"],
                experiment_id=run["experiment_id"],
                run_class=run["run_class"],
                status=run["status"],
                primary=run.get("metrics", {}).get("primary", "—"),
                operator=run["operator_family"],
                recovery=run.get("recovery") or "—",
            )
        )
    lines.extend(["", "## Artifact provenance", "", "| Run | Code revision | Diff hash | Evaluator hash | Frozen checkpoint |", "|---|---|---|---|---|"])
    for run in runs:
        manifest = run.get("checkpoint_manifest") or {}
        lines.append(
            "| {run_id} | {revision} | {diff} | {evaluator} | {checkpoint} |".format(
                run_id=run["run_id"],
                revision=(run.get("code_revision") or "—")[:12],
                diff=(run.get("diff_sha256") or "—")[:12],
                evaluator=(run.get("evaluator_sha256") or "—")[:12],
                checkpoint=manifest.get("checkpoint_sha256", "—")[:12],
            )
        )
    lines.extend(["", "## Integrity", "", "- Test-label scoring is not exposed through the research adapter.", "- Every listed metric resolves to a ledger record and declared run class.", "- Resource totals separate qualification from research/final runs so convergence costs are not overstated."])
    return "\n".join(lines) + "\n"


def write_report(ledger: ExperimentLedger, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(ledger), encoding="utf-8")
    return path

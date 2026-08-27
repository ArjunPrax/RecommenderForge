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
    lines = [
        "# Autonomous Research Run Report",
        "",
        "## Run summary",
        "",
        f"- Total runs: {len(runs)}",
        f"- Statuses: {dict(sorted(counts.items()))}",
        f"- Run classes: {dict(sorted(classes.items()))}",
        f"- Resource totals: {dict(sorted(resources.items()))}",
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
    lines.extend(["", "## Integrity", "", "- Test-label scoring is not exposed through the research adapter.", "- Every listed metric resolves to a ledger record and declared run class."])
    return "\n".join(lines) + "\n"


def write_report(ledger: ExperimentLedger, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(ledger), encoding="utf-8")
    return path

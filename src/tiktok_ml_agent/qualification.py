"""Deterministic end-to-end qualification workflow.

This is deliberately data-free. It proves the control plane, recovery, memory,
convergence rehearsal, checkpoint binding, output validation, and report export
before the real benchmark data is downloaded.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from .benchmark import BenchmarkAdapter
from .contracts import (
    BenchmarkSpec,
    CheckpointManifest,
    EvidenceCard,
    ExperimentSpec,
    OperatorFamily,
    RunClass,
    TestAccessError,
    hash_file,
)
from .controller import CandidateBatch, ConvergenceTracker, ExecutionResult, ResearchController
from .ledger import ExperimentLedger
from .memory import KnowledgeBase, MemoryManager
from .reporting import write_report


def _qualification_evaluator(user_ids: list[str], labels: list[int], scores: list[float]) -> dict[str, float]:
    """Synthetic evaluator used only to exercise platform mechanics, never benchmark claims."""
    grouped: dict[str, list[tuple[float, int]]] = {}
    for user_id, label, score in zip(user_ids, labels, scores):
        grouped.setdefault(user_id, []).append((score, label))
    top_hit = sum(int(max(rows, key=lambda row: row[0])[1] == 1) for rows in grouped.values()) / len(grouped)
    return {"top_hit": top_hit, "primary": top_hit}


def _config_hash(configuration: dict[str, object]) -> str:
    return sha256(json.dumps(configuration, sort_keys=True).encode()).hexdigest()


def run_qualification(output_dir: str | Path) -> dict[str, str | bool | int]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    spec = BenchmarkSpec(
        benchmark_id="qualification-fixture",
        profile_id="synthetic-v1",
        label="fixture_positive",
        metrics=("top_hit",),
        source_note="Synthetic qualification-only contract; not organizer evaluation.",
    )
    adapter = BenchmarkAdapter(spec, _qualification_evaluator)
    controller = ResearchController(spec, ledger)
    memory = MemoryManager(ledger)
    knowledge = KnowledgeBase(
        [
            EvidenceCard(
                evidence_id="KB-001",
                title="Qualification control-plane fixture",
                source="internal deterministic fixture",
                claim="A bounded candidate batch should retain both success and recovery evidence.",
                assumptions=("synthetic scores are used only for system qualification",),
                operator_families=(OperatorFamily.HYPERPARAMETER,),
                applicability="Qualification run",
            )
        ]
    )
    retrieved = knowledge.retrieve("candidate recovery evidence", limit=1)
    users = ["u1", "u1", "u2", "u2"]
    labels = [1, 0, 1, 0]
    rows = [("u1", "v1"), ("u1", "v2"), ("u2", "v3"), ("u2", "v4")]

    def execute(candidate: ExperimentSpec) -> ExecutionResult:
        if candidate.configuration.get("inject_failure"):
            raise RuntimeError("controlled qualification failure")
        scores = [float(value) for value in candidate.configuration["scores"]]
        metrics = adapter.score_development("valid", users, labels, scores)
        checkpoint = output_dir / "checkpoints" / f"{candidate.configuration['checkpoint_name']}.json"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(json.dumps({"scores": scores, "experiment": candidate.experiment_id}), encoding="utf-8")
        prediction_hash = sha256(json.dumps(scores).encode()).hexdigest()
        manifest = CheckpointManifest(
            checkpoint_path=str(checkpoint),
            checkpoint_sha256=hash_file(checkpoint),
            code_revision="qualification-fixture",
            data_fingerprint="qualification-fixture-v1",
            evaluator_sha256=None,
            configuration_sha256=_config_hash(dict(candidate.configuration)),
            validation_prediction_sha256=prediction_hash,
            validation_metrics=metrics,
        )
        return ExecutionResult(
            metrics=metrics,
            checkpoint_manifest=manifest,
            diagnosis={
                "summary": "Synthetic candidate preserved the expected positive ordering.",
                "evidence_strength": "qualification_fixture",
                "alternative_explanations": ["This is a system test, not a model-quality claim."],
            },
            resource_usage={"llm_input_tokens": 0.0, "llm_output_tokens": 0.0, "cpu_seconds": 0.0},
        )

    first_batch = CandidateBatch(
        batch_id="qualification-batch-1",
        parent_run_id=None,
        parent_checkpoint_sha256=None,
        candidates=(
            ExperimentSpec(
                experiment_id="EXP-003",
                run_class=RunClass.QUALIFICATION,
                operator_family=OperatorFamily.HYPERPARAMETER,
                hypothesis="A deterministic ordered fixture should produce a valid measured checkpoint.",
                expected_mechanism="Correct ranking preserves the positive item at the top for each fixture user.",
                evidence_ids=tuple(card.evidence_id for card in retrieved),
                configuration={"scores": [0.8, 0.2, 0.7, 0.3], "checkpoint_name": "winner"},
            ),
            ExperimentSpec(
                experiment_id="EXP-003",
                run_class=RunClass.QUALIFICATION,
                operator_family=OperatorFamily.HYPERPARAMETER,
                hypothesis="A controlled failure must be recovered and recorded.",
                expected_mechanism="The controller returns to the immutable parent after an exception.",
                evidence_ids=("KB-001",),
                configuration={"inject_failure": True, "checkpoint_name": "failure"},
            ),
            ExperimentSpec(
                experiment_id="EXP-003",
                run_class=RunClass.QUALIFICATION,
                operator_family=OperatorFamily.HYPERPARAMETER,
                hypothesis="A sibling candidate starts from the shared parent rather than another sibling diff.",
                expected_mechanism="Sibling isolation retains an independently valid result.",
                evidence_ids=("KB-001",),
                configuration={"scores": [0.75, 0.25, 0.65, 0.35], "checkpoint_name": "sibling"},
            ),
        ),
    )
    first_records = controller.execute_batch(first_batch, execute)
    winner = next(record for record in first_records if record.status.value == "succeeded")
    second_batch = CandidateBatch(
        batch_id="qualification-batch-2",
        parent_run_id=winner.run_id,
        parent_checkpoint_sha256=winner.checkpoint_manifest["checkpoint_sha256"] if winner.checkpoint_manifest else None,
        candidates=(
            ExperimentSpec(
                experiment_id="EXP-003",
                run_class=RunClass.QUALIFICATION,
                operator_family=OperatorFamily.HYPERPARAMETER,
                hypothesis="Repeated fixture performance supplies qualification convergence evidence.",
                expected_mechanism="No significant improvement accumulates stagnation.",
                parent_run_id=winner.run_id,
                parent_checkpoint_sha256=winner.checkpoint_manifest["checkpoint_sha256"] if winner.checkpoint_manifest else None,
                evidence_ids=("KB-001",),
                configuration={"scores": [0.7, 0.3, 0.7, 0.3], "checkpoint_name": "repeat-1"},
            ),
            ExperimentSpec(
                experiment_id="EXP-003",
                run_class=RunClass.QUALIFICATION,
                operator_family=OperatorFamily.HYPERPARAMETER,
                hypothesis="A final repeated fixture completes the convergence rehearsal.",
                expected_mechanism="Three non-significant results after the best result satisfy qualification stagnation.",
                parent_run_id=winner.run_id,
                parent_checkpoint_sha256=winner.checkpoint_manifest["checkpoint_sha256"] if winner.checkpoint_manifest else None,
                evidence_ids=("KB-001",),
                configuration={"scores": [0.6, 0.4, 0.7, 0.3], "checkpoint_name": "repeat-2"},
            ),
        ),
    )
    second_records = controller.execute_batch(second_batch, execute)
    timeout_candidate = ExperimentSpec(
        experiment_id="EXP-003",
        run_class=RunClass.QUALIFICATION,
        operator_family=OperatorFamily.HYPERPARAMETER,
        hypothesis="An exhausted candidate budget must be recorded as a timeout recovery.",
        expected_mechanism="The controller interrupts execution before an expired candidate can stall the batch.",
        evidence_ids=("KB-001",),
        configuration={"checkpoint_name": "timeout"},
        compute_budget_seconds=0,
    )
    timeout_record = controller.execute_batch(
        CandidateBatch("qualification-timeout", None, None, (timeout_candidate,)), execute
    )[0]
    if timeout_record.status.value != "recovered" or timeout_record.recovery != "terminate_stalled_candidate_and_return_to_parent":
        raise RuntimeError("qualification timeout recovery was not recorded")
    rehearsal = ConvergenceTracker(spec.epsilon, spec.patience)
    converged = False
    for record in [*first_records, *second_records]:
        if record.status.value == "succeeded":
            converged = rehearsal.observe(record.run_id, record.metrics["primary"], eligible=True) or converged

    try:
        adapter.forbid_test_labels("test", include_labels=True)
    except TestAccessError as error:
        ledger.append_event(winner.run_id, "test_access_denied", {"error": str(error)})

    winner_manifest = winner.checkpoint_manifest
    if winner_manifest is None:
        raise RuntimeError("qualification winner has no checkpoint manifest")
    winner_scores = json.loads(Path(winner_manifest["checkpoint_path"]).read_text(encoding="utf-8"))["scores"]
    submission = [(index, user_id, video_id, float(score)) for index, ((user_id, video_id), score) in enumerate(zip(rows, winner_scores))]
    adapter.validate_submission_rows(rows, submission)
    submission_path = output_dir / "qualification_submission.json"
    submission_path.write_text(json.dumps(submission), encoding="utf-8")
    snapshot = memory.consolidate() if memory.should_consolidate(projected_prompt_tokens=20_000) else None
    report_path = write_report(ledger, output_dir / "qualification_report.md")
    ledger.close()
    return {
        "ledger": str(output_dir / "ledger.sqlite"),
        "report": str(report_path),
        "submission": str(submission_path),
        "converged": converged,
        "memory_snapshot": int(snapshot is not None),
    }

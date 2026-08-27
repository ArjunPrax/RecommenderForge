"""First complete research loop over the real KuaiRand validation benchmark."""

from __future__ import annotations

from pathlib import Path

from .contracts import EvidenceCard, OperatorFamily, RunClass
from .controller import ResearchController
from .kuairand import starter_kuairand_pure_spec
from .ledger import ExperimentLedger
from .memory import KnowledgeBase, MemoryManager
from .planner import FixedPlanner, PlannerContext
from .reporting import write_report
from .research_runner import execute_ranking_candidate


def _ranking_knowledge() -> KnowledgeBase:
    return KnowledgeBase(
        [
            EvidenceCard(
                evidence_id="KB-002",
                title="Bayesian Personalized Ranking",
                source="Rendle et al. (2009), BPR: Bayesian Personalized Ranking from Implicit Feedback",
                claim="Pairwise preference optimization can directly train a latent-factor model to rank observed positives above negatives.",
                assumptions=("logged same-user positive and negative impressions supply valid pair candidates",),
                operator_families=(OperatorFamily.LOSS_OBJECTIVE,),
                applicability="First loss-objective comparison on KuaiRand-Pure.",
                risks=("pair sampling can overrepresent users with many positives",),
            ),
            EvidenceCard(
                evidence_id="KB-003",
                title="Exact within-user listwise objective",
                source="Interpretation - dataset-specific objective derived from the organizer's within-user ranking evaluator",
                claim="Complete logged impression lists can support a grouped listwise softmax without cross-user comparisons.",
                assumptions=("each group remains complete during batching",),
                operator_families=(OperatorFamily.LOSS_OBJECTIVE,),
                applicability="Comparator for BPR; not a claimed external result.",
                risks=("users with no positive labels do not contribute a listwise gradient",),
            ),
        ]
    )


def run_autonomous_ranking(
    *,
    repository_root: str | Path,
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Plan, execute, recover, ledger, and report an initial objective batch.

    The default is an offline deterministic policy so the workflow is fully
    reproducible without credentials. `OpenAIResponsesPlanner` can replace it
    without changing the contract or execution permissions.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir)
    ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = _ranking_knowledge()
    context = PlannerContext(
        goal="Compare first-round same-user ranking objectives against the reproduced pointwise FM control.",
        experiment_ids=("EXP-004A", "EXP-004B"),
        run_class=RunClass.RESEARCH,
        parent_run_id=None,
        parent_checkpoint_sha256=None,
        allowed_operator_families=(OperatorFamily.LOSS_OBJECTIVE,),
        allowed_paths=(),
        token_budget=0,
        compute_budget_seconds=3600,
    )
    planner = FixedPlanner(
        {
            "rationale": (
                "Run BPR and an exact grouped-listwise loss as sibling objective changes. "
                "Both retain the FM features, optimizer, train/validation split, and five-seed protocol."
            ),
            "candidates": [
                {
                    "experiment_id": "EXP-004A",
                    "operator_family": "loss_objective",
                    "hypothesis": "BPR improves validation ranking over pointwise FM.",
                    "expected_mechanism": "same-user positive impressions receive larger scores than sampled negatives.",
                    "evidence_ids": ["KB-002"],
                    "configuration": {"objective": "bpr", "seeds": [0, 1, 2, 3, 4]},
                    "controlled_variables": ["FM fields", "optimizer", "train/validation split", "seed set"],
                },
                {
                    "experiment_id": "EXP-004B",
                    "operator_family": "loss_objective",
                    "hypothesis": "A complete same-user listwise objective improves validation ranking over pointwise FM.",
                    "expected_mechanism": "each logged user impression list concentrates score on positive items.",
                    "evidence_ids": ["KB-003"],
                    "configuration": {"objective": "listwise", "seeds": [0, 1, 2, 3, 4]},
                    "controlled_variables": ["FM fields", "optimizer", "train/validation split", "seed set"],
                },
            ],
        }
    )
    plan = planner.plan(context, knowledge)
    controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(
        plan.batch,
        lambda candidate: execute_ranking_candidate(
            candidate,
            repository_root=repository_root,
            starter_kit_dir=starter_kit_dir,
            data_dir=data_dir,
            artifact_root=output_dir / "artifacts",
        ),
    )
    for record in records:
        ledger.append_event(
            record.run_id,
            "planner_decision",
            {
                "rationale": plan.rationale,
                "provider": "fixed_offline_policy",
                "input_tokens": plan.input_tokens,
                "output_tokens": plan.output_tokens,
            },
        )
    converged = controller.observe_for_convergence(records)
    snapshot = MemoryManager(ledger).consolidate()
    report = write_report(ledger, output_dir / "report.md")
    response = {
        "ledger": str(output_dir / "ledger.sqlite"),
        "report": str(report),
        "memory_snapshot": snapshot["snapshot_id"],
        "converged": converged,
        "runs": [record.run_id for record in records],
    }
    ledger.close()
    return response


def run_autonomous_history(
    *,
    repository_root: str | Path,
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    parent_ledger_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Run the history-cross candidate from the frozen BPR parent manifest."""
    parent_ledger = ExperimentLedger(parent_ledger_path)
    try:
        parent = next(
            (run for run in parent_ledger.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"),
            None,
        )
    finally:
        parent_ledger.close()
    if parent is None or not parent.get("checkpoint_manifest"):
        raise ValueError("history research requires a succeeded EXP-004A parent with a checkpoint manifest")
    parent_hash = parent["checkpoint_manifest"].get("checkpoint_sha256")
    if not parent_hash:
        raise ValueError("history research parent is missing a checkpoint hash")
    parent_prediction_path = Path(parent["checkpoint_manifest"]["checkpoint_path"]).with_suffix(".validation.npy")
    if not parent_prediction_path.is_file():
        raise ValueError("history research parent validation predictions are unavailable for ordering audit")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir)
    ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase(
        [
            EvidenceCard(
                evidence_id="KB-004",
                title="Strictly-prior history crossed with candidate features",
                source="Interpretation - recommender feature design constrained by within-user ranking and temporal leakage controls",
                claim="A frozen user long-view history can only affect within-user order through interactions with candidate features.",
                assumptions=("validation features use training-period history only",),
                operator_families=(OperatorFamily.TEMPORAL_HISTORY,),
                applicability="BPR FM extension after the frozen EXP-004A parent.",
                risks=("user-only terms cannot reorder a user's candidates; temporal leakage must be mechanically prevented",),
            )
        ]
    )
    context = PlannerContext(
        goal="Test whether a strictly-earlier train-only long-view history field improves BPR through candidate-feature FM crosses.",
        experiment_ids=("EXP-005",),
        run_class=RunClass.RESEARCH,
        parent_run_id=parent["run_id"],
        parent_checkpoint_sha256=str(parent_hash),
        allowed_operator_families=(OperatorFamily.TEMPORAL_HISTORY,),
        allowed_paths=(),
        token_budget=0,
        compute_budget_seconds=1800,
    )
    planner = FixedPlanner(
        {
            "rationale": "Keep the BPR objective fixed and add one temporally safe history field that FM can cross with each candidate's fields.",
            "candidates": [
                {
                    "experiment_id": "EXP-005",
                    "operator_family": "temporal_history",
                    "hypothesis": "Frozen train-only user history crosses improve BPR validation ranking.",
                    "expected_mechanism": "the history bucket interacts with video, author, tab, and duration fields rather than acting as a user-constant score.",
                    "evidence_ids": ["KB-004"],
                    "configuration": {
                        "objective": "bpr",
                        "history_cross": True,
                        "seeds": [0, 1, 2, 3, 4],
                        "parent_validation_prediction_path": str(parent_prediction_path),
                    },
                    "controlled_variables": ["BPR loss", "FM optimizer", "train/validation split", "seed set"],
                }
            ],
        }
    )
    plan = planner.plan(context, knowledge)
    controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(
        plan.batch,
        lambda candidate: execute_ranking_candidate(
            candidate,
            repository_root=repository_root,
            starter_kit_dir=starter_kit_dir,
            data_dir=data_dir,
            artifact_root=output_dir / "artifacts",
        ),
    )
    for record in records:
        ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    converged = controller.observe_for_convergence(records)
    snapshot = MemoryManager(ledger).consolidate()
    report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": converged, "runs": [record.run_id for record in records]}
    ledger.close()
    return response

"""First complete research loop over the real KuaiRand validation benchmark."""

from __future__ import annotations

import json
from pathlib import Path

from .contracts import EvidenceCard, OperatorFamily, RunClass
from .controller import ResearchController
from .kuairand import starter_kuairand_pure_spec
from .ledger import ExperimentLedger
from .memory import KnowledgeBase, MemoryManager
from .planner import FixedPlanner, PlannerContext
from .reporting import write_report
from .research_runner import execute_ranking_candidate
from .ensemble_runner import execute_rank_ensemble, execute_three_rank_ensemble


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


def run_autonomous_item_tab_history(
    *,
    repository_root: str | Path,
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    parent_ledger_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Test a strict-prior, global video×tab history field from frozen BPR."""
    parent_ledger = ExperimentLedger(parent_ledger_path)
    try:
        parent = next(
            (run for run in parent_ledger.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"),
            None,
        )
    finally:
        parent_ledger.close()
    if parent is None or not parent.get("checkpoint_manifest"):
        raise ValueError("video-tab research requires a succeeded EXP-004A parent with a checkpoint manifest")
    parent_hash = parent["checkpoint_manifest"].get("checkpoint_sha256")
    if not parent_hash:
        raise ValueError("video-tab research parent is missing a checkpoint hash")
    parent_prediction_path = Path(parent["checkpoint_manifest"]["checkpoint_path"]).with_suffix(".validation.npy")
    if not parent_prediction_path.is_file():
        raise ValueError("video-tab research parent validation predictions are unavailable for ordering audit")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir)
    ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase(
        [
            EvidenceCard(
                evidence_id="KB-013",
                title="Strictly-prior candidate video×tab history",
                source="Interpretation - train-only candidate cross motivated by R018's bounded item×tab scale result",
                claim="A global video×tab engagement bucket can change within-user ranking because it varies by candidate, provided it is strictly prior for training and frozen after training for evaluation.",
                assumptions=("video ID and tab are present at inference", "only permitted training labels update the bucket"),
                operator_families=(OperatorFamily.CANDIDATE_CROSS,),
                applicability="Candidate-specific BPR FM extension after the frozen EXP-004A parent.",
                risks=("target leakage if a row updates its own feature", "global buckets may be too sparse or redundant with FM item/tab fields"),
            )
        ]
    )
    context = PlannerContext(
        goal="Test whether strictly-prior global video×tab history supplies a candidate-specific feature beyond BPR FM fields.",
        experiment_ids=("EXP-016",),
        run_class=RunClass.RESEARCH,
        parent_run_id=parent["run_id"],
        parent_checkpoint_sha256=str(parent_hash),
        allowed_operator_families=(OperatorFamily.CANDIDATE_CROSS,),
        allowed_paths=(),
        token_budget=0,
        compute_budget_seconds=1800,
    )
    planner = FixedPlanner(
        {
            "rationale": "Keep the BPR objective fixed and add one global candidate-specific history field. Its construction is strict-prior for train and train-frozen for validation/submission.",
            "candidates": [
                {
                    "experiment_id": "EXP-016",
                    "operator_family": "candidate_cross",
                    "hypothesis": "Strictly-prior video×tab buckets improve BPR validation ranking beyond the frozen BPR parent.",
                    "expected_mechanism": "the bucket varies across candidate video/tab pairs within a user list and is crossed by FM with the base fields.",
                    "evidence_ids": ["KB-013"],
                    "configuration": {
                        "objective": "bpr",
                        "item_tab_history_cross": True,
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


def run_autonomous_user_author_history(
    *,
    repository_root: str | Path,
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    parent_ledger_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Test strict-prior personalised user×author history from frozen BPR."""
    parent_ledger = ExperimentLedger(parent_ledger_path)
    try:
        parent = next((run for run in parent_ledger.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"), None)
    finally:
        parent_ledger.close()
    if parent is None or not parent.get("checkpoint_manifest"):
        raise ValueError("user-author research requires a succeeded EXP-004A parent with a checkpoint manifest")
    parent_hash = parent["checkpoint_manifest"].get("checkpoint_sha256")
    if not parent_hash:
        raise ValueError("user-author research parent is missing a checkpoint hash")
    parent_prediction_path = Path(parent["checkpoint_manifest"]["checkpoint_path"]).with_suffix(".validation.npy")
    if not parent_prediction_path.is_file():
        raise ValueError("user-author research parent validation predictions are unavailable for ordering audit")
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir)
    ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(
        evidence_id="KB-016", title="Strictly-prior user-author affinity history",
        source="Interpretation - personalised candidate-author history from permitted training impressions",
        claim="A user's earlier response rate for a candidate's author can alter within-user order while remaining label-free at evaluation time.",
        assumptions=("author identity is available before ranking", "only train long_view labels update affinity state"),
        operator_families=(OperatorFamily.CANDIDATE_CROSS,),
        applicability="Personalised BPR FM extension after the frozen EXP-004A parent.",
        risks=("target leakage if evaluation labels update state", "sparse authors can collapse to the zero-history bucket"),
    )])
    context = PlannerContext(
        goal="Test whether strictly-prior user×author affinity adds a personalised candidate-specific signal beyond BPR FM fields.",
        experiment_ids=("EXP-018",), run_class=RunClass.RESEARCH,
        parent_run_id=parent["run_id"], parent_checkpoint_sha256=str(parent_hash),
        allowed_operator_families=(OperatorFamily.CANDIDATE_CROSS,), allowed_paths=(),
        token_budget=0, compute_budget_seconds=1800,
    )
    planner = FixedPlanner({"rationale": "Keep BPR fixed and add one personal candidate-author feature. Its state is strict-prior for train and frozen from training for validation/submission.", "candidates": [{
        "experiment_id": "EXP-018", "operator_family": "candidate_cross",
        "hypothesis": "Strictly-prior user-author buckets improve BPR validation ranking beyond the frozen BPR parent.",
        "expected_mechanism": "author affinity varies across a user's candidate videos and is crossed by FM with the base fields.",
        "evidence_ids": ["KB-016"],
        "configuration": {"objective": "bpr", "user_author_history_cross": True, "seeds": [0, 1, 2, 3, 4], "parent_validation_prediction_path": str(parent_prediction_path)},
        "controlled_variables": ["BPR loss", "FM optimizer", "train/validation split", "seed set"],
    }]})
    plan = planner.plan(context, knowledge); controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_ranking_candidate(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records:
        ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    converged = controller.observe_for_convergence(records)
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": converged, "runs": [record.run_id for record in records]}
    ledger.close(); return response


def run_autonomous_multitask(
    *,
    repository_root: str | Path,
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    parent_ledger_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Run train-only multi-feedback BPR from a frozen BPR parent."""
    parent_ledger = ExperimentLedger(parent_ledger_path)
    try:
        parent = next((run for run in parent_ledger.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"), None)
    finally:
        parent_ledger.close()
    if parent is None or not parent.get("checkpoint_manifest"):
        raise ValueError("multi-task research requires a succeeded EXP-004A parent manifest")
    parent_hash = parent["checkpoint_manifest"].get("checkpoint_sha256")
    if not parent_hash:
        raise ValueError("multi-task parent is missing a checkpoint hash")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir)
    ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase(
        [
            EvidenceCard(
                evidence_id="KB-005",
                title="Shared representation across observed feedback",
                source="Interpretation - multi-task learning candidate using organizer-provided train-only click, like, and follow outcomes",
                claim="Auxiliary feedback losses may regularize a shared representation used by the primary long-view ranking task.",
                assumptions=("auxiliary outcomes are read only from the training split",),
                operator_families=(OperatorFamily.MULTI_TASK,),
                applicability="Controlled extension of BPR FM.",
                risks=("auxiliary objectives can distract from the primary ranking metric",),
            )
        ]
    )
    context = PlannerContext(
        goal="Test whether train-only click, like, and follow supervision improves the primary BPR long-view ranking.",
        experiment_ids=("EXP-006",),
        run_class=RunClass.RESEARCH,
        parent_run_id=parent["run_id"],
        parent_checkpoint_sha256=str(parent_hash),
        allowed_operator_families=(OperatorFamily.MULTI_TASK,),
        allowed_paths=(),
        token_budget=0,
        compute_budget_seconds=1800,
    )
    planner = FixedPlanner(
        {
            "rationale": "Keep BPR and the FM backbone fixed; add train-only auxiliary feedback BCE through task-specific heads.",
            "candidates": [{
                "experiment_id": "EXP-006",
                "operator_family": "multi_task",
                "hypothesis": "Shared train-only click/like/follow supervision improves BPR primary validation score.",
                "expected_mechanism": "auxiliary gradients regularize the shared FM interactions while the long-view BPR head remains the evaluated scorer.",
                "evidence_ids": ["KB-005"],
                "configuration": {"objective": "bpr", "auxiliary_weight": 0.15, "seeds": [0, 1, 2, 3, 4]},
                "controlled_variables": ["BPR loss", "FM fields", "train/validation split", "seed set"],
            }],
        }
    )
    plan = planner.plan(context, knowledge)
    controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_ranking_candidate(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records:
        ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    converged = controller.observe_for_convergence(records)
    snapshot = MemoryManager(ledger).consolidate()
    report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": converged, "runs": [record.run_id for record in records]}
    ledger.close()
    return response


def run_autonomous_watchtime(
    *,
    repository_root: str | Path,
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    parent_ledger_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Test train-only watch-completion supervision from the frozen BPR parent."""
    parent_ledger = ExperimentLedger(parent_ledger_path)
    try:
        parent = next((run for run in parent_ledger.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"), None)
    finally:
        parent_ledger.close()
    if parent is None or not parent.get("checkpoint_manifest"):
        raise ValueError("watch-time research requires a succeeded EXP-004A parent manifest")
    parent_hash = parent["checkpoint_manifest"].get("checkpoint_sha256")
    if not parent_hash:
        raise ValueError("watch-time parent is missing a checkpoint hash")
    parent_prediction_path = str(Path(parent["checkpoint_manifest"]["checkpoint_path"]).with_suffix(".validation.npy"))
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir); ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(
        evidence_id="KB-010",
        title="Watch-completion auxiliary supervision",
        source="Interpretation - organizer-provided train-only play_time_ms normalized by duration_ms",
        claim="A bounded watch-completion loss may teach the shared FM preference signal not captured by binary long_view alone.",
        assumptions=("play_time_ms is requested only from training rows", "completion is clipped to [0, 1]"),
        operator_families=(OperatorFamily.MULTI_TASK,),
        applicability="Controlled BPR auxiliary-objective candidate.",
        risks=("post-exposure outcomes must never be read from validation or test", "the auxiliary may distract from ranking"),
    )])
    context = PlannerContext(
        goal="Test whether train-only normalized watch completion improves long-view BPR ranking.",
        experiment_ids=("EXP-007",), run_class=RunClass.RESEARCH,
        parent_run_id=parent["run_id"], parent_checkpoint_sha256=str(parent_hash),
        allowed_operator_families=(OperatorFamily.MULTI_TASK,), allowed_paths=(), token_budget=0, compute_budget_seconds=1800,
    )
    planner = FixedPlanner({
        "rationale": "Keep BPR and the FM fields fixed; add one train-only, clipped watch-completion BCE head.",
        "candidates": [{
            "experiment_id": "EXP-007", "operator_family": "multi_task",
            "hypothesis": "Train-only watch-completion supervision improves BPR validation primary.",
            "expected_mechanism": "a shared representation receives denser preference gradients while the evaluated BPR head remains unchanged.",
            "evidence_ids": ["KB-010"],
            "configuration": {"objective": "bpr", "auxiliary_task": "watch_completion", "auxiliary_weight": 0.10, "seeds": [0, 1, 2, 3, 4], "parent_validation_prediction_path": parent_prediction_path},
            "controlled_variables": ["BPR loss", "FM fields", "train/validation split", "seed set"],
        }],
    })
    plan = planner.plan(context, knowledge); controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_ranking_candidate(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records:
        ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": controller.observe_for_convergence(records), "runs": [record.run_id for record in records]}
    ledger.close(); return response


def run_autonomous_negative_sampling(
    *,
    repository_root: str | Path,
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    parent_ledger_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Compare a predeclared denser same-user BPR negative sampler."""
    source = ExperimentLedger(parent_ledger_path)
    try:
        parent = next((run for run in source.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"), None)
    finally:
        source.close()
    if not parent or not parent.get("checkpoint_manifest"):
        raise ValueError("negative-sampling research requires a succeeded EXP-004A parent")
    parent_manifest = parent["checkpoint_manifest"]
    parent_prediction_path = str(Path(parent_manifest["checkpoint_path"]).with_suffix(".validation.npy"))
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir); ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(
        evidence_id="KB-011", title="Multiple within-user BPR negatives",
        source="Rendle et al. (2009), BPR: Bayesian Personalized Ranking from Implicit Feedback",
        claim="Drawing more sampled negatives per observed preference can cover a wider set of same-user non-positive impressions.",
        assumptions=("negatives remain within the same user group",),
        operator_families=(OperatorFamily.SAMPLING,), applicability="Controlled BPR sampler comparison.",
        risks=("more repeated negatives can increase compute without new information",),
    )])
    context = PlannerContext(
        goal="Test a denser within-user BPR negative sampler against the frozen BPR parent.", experiment_ids=("EXP-013",),
        run_class=RunClass.RESEARCH, parent_run_id=parent["run_id"], parent_checkpoint_sha256=parent_manifest["checkpoint_sha256"],
        allowed_operator_families=(OperatorFamily.SAMPLING,), allowed_paths=(), token_budget=0, compute_budget_seconds=3600,
    )
    planner = FixedPlanner({"rationale": "Keep the loss, features, splits, and seeds fixed; draw three same-user negatives per positive.", "candidates": [{
        "experiment_id": "EXP-013", "operator_family": "sampling", "hypothesis": "Three same-user BPR negatives per positive improve validation ranking.",
        "expected_mechanism": "a positive is compared with more of its user's exposed non-positive videos each epoch.",
        "evidence_ids": ["KB-011"],
        "configuration": {"objective": "bpr", "negatives_per_positive": 3, "seeds": [0, 1, 2, 3, 4], "parent_validation_prediction_path": parent_prediction_path},
        "controlled_variables": ["BPR loss", "FM fields", "train/validation split", "seed set"],
    }]})
    plan = planner.plan(context, knowledge); controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_ranking_candidate(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records:
        ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": controller.observe_for_convergence(records), "runs": [record.run_id for record in records]}
    ledger.close(); return response


def run_autonomous_lambda_ranking(
    *,
    repository_root: str | Path,
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    parent_ledger_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Evaluate a top-five-aware Lambda-BPR mixture from the BPR control."""
    source = ExperimentLedger(parent_ledger_path)
    try:
        parent = next((run for run in source.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"), None)
    finally:
        source.close()
    if not parent or not parent.get("checkpoint_manifest"):
        raise ValueError("Lambda-BPR research requires a succeeded EXP-004A parent")
    parent_manifest = parent["checkpoint_manifest"]
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir); ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(
        evidence_id="KB-012", title="LambdaRank top-k swap weighting",
        source="Burges et al. (2010), From RankNet to LambdaRank to LambdaMART: An Overview",
        claim="Pairwise ranking gradients can be weighted by the metric change caused by a predicted-rank swap.",
        assumptions=("detached predicted ranks are computed from complete same-user groups", "nDCG@5 swap gain is the intended local weighting signal"),
        operator_families=(OperatorFamily.LOSS_OBJECTIVE,), applicability="Top-five-aware BPR comparison.",
        risks=("sparse top-five weights can reduce signal; the BPR component remains in the mixture",),
    )])
    context = PlannerContext(
        goal="Test whether an nDCG@5-aware pairwise weighting improves the BPR ranking objective.", experiment_ids=("EXP-014",),
        run_class=RunClass.RESEARCH, parent_run_id=parent["run_id"], parent_checkpoint_sha256=parent_manifest["checkpoint_sha256"],
        allowed_operator_families=(OperatorFamily.LOSS_OBJECTIVE,), allowed_paths=(), token_budget=0, compute_budget_seconds=3600,
    )
    planner = FixedPlanner({"rationale": "Keep BPR fields, optimizer, splits, and seeds fixed; mix equal BPR and detached nDCG@5 swap-gain-weighted pair losses.", "candidates": [{
        "experiment_id": "EXP-014", "operator_family": "loss_objective", "hypothesis": "A top-five-aware Lambda-BPR mixture improves primary validation score over BPR.",
        "expected_mechanism": "same-user pair gradients are upweighted when swapping their current predicted ranks could change nDCG@5.",
        "evidence_ids": ["KB-012"],
        "configuration": {"objective": "lambda_bpr", "lambda_mix": 0.5, "seeds": [0, 1, 2, 3, 4], "parent_validation_prediction_path": str(Path(parent_manifest["checkpoint_path"]).with_suffix(".validation.npy"))},
        "controlled_variables": ["FM fields", "optimizer", "train/validation split", "seed set", "same-user pair sampler"],
    }]})
    plan = planner.plan(context, knowledge); controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_ranking_candidate(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records:
        ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": controller.observe_for_convergence(records), "runs": [record.run_id for record in records]}
    ledger.close(); return response


def run_autonomous_ensemble(
    *, repository_root: str | Path, starter_kit_dir: str | Path, data_dir: str | Path,
    bpr_ledger_path: str | Path, history_ledger_path: str | Path, output_dir: str | Path,
) -> dict[str, object]:
    """Compare declared rank blends built only from frozen component artifacts."""
    bpr_ledger = ExperimentLedger(bpr_ledger_path)
    history_ledger = ExperimentLedger(history_ledger_path)
    try:
        bpr = next((run for run in bpr_ledger.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"), None)
        history = next((run for run in history_ledger.list_runs() if run["experiment_id"] == "EXP-005" and run["status"] == "succeeded"), None)
    finally:
        bpr_ledger.close(); history_ledger.close()
    if not bpr or not history or not bpr.get("checkpoint_manifest") or not history.get("checkpoint_manifest"):
        raise ValueError("ensemble requires succeeded checkpoint-backed EXP-004A and EXP-005 components")
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir)
    ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(
        evidence_id="KB-006", title="Rank ensemble of complementary objectives", source="Interpretation - component blend over frozen validation predictions",
        claim="Rank-space blending can combine independently trained objectives while preserving each component's within-user ordering contribution.",
        assumptions=("component checkpoints and predictions are immutable",), operator_families=(OperatorFamily.ENSEMBLE,),
        applicability="BPR plus strict-history BPR blend.", risks=("weight selection consumes validation feedback and must be logged",),
    )])
    context = PlannerContext(goal="Evaluate a declared five-seed rank blend of frozen BPR and history-cross components.", experiment_ids=("EXP-009",), run_class=RunClass.RESEARCH, parent_run_id=bpr["run_id"], parent_checkpoint_sha256=bpr["checkpoint_manifest"]["checkpoint_sha256"], allowed_operator_families=(OperatorFamily.ENSEMBLE,), allowed_paths=(), token_budget=0, compute_budget_seconds=600)
    planner = FixedPlanner({"rationale": "Blend frozen component ranks; do not retrain components or use test labels.", "candidates": [{"experiment_id": "EXP-009", "operator_family": "ensemble", "hypothesis": "A rank blend of BPR and history-cross BPR improves validation primary relative to either component.", "expected_mechanism": "components make different within-user ordering errors that rank blending can reduce.", "evidence_ids": ["KB-006"], "configuration": {"bpr_ledger": str(bpr_ledger_path), "history_ledger": str(history_ledger_path), "bpr_weights": [0.25, 0.5, 0.75], "seeds": [0, 1, 2, 3, 4]}, "controlled_variables": ["frozen component checkpoints", "validation rows", "seed set"]}]})
    plan = planner.plan(context, knowledge)
    controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_rank_ensemble(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records:
        ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": controller.observe_for_convergence(records), "runs": [record.run_id for record in records]}
    ledger.close(); return response


def run_autonomous_temporal(
    *, repository_root: str | Path, starter_kit_dir: str | Path, data_dir: str | Path,
    parent_ledger_path: str | Path, output_dir: str | Path,
) -> dict[str, object]:
    """Test an inference-available calendar cross from the frozen BPR parent."""
    parent_ledger = ExperimentLedger(parent_ledger_path)
    try:
        parent = next((run for run in parent_ledger.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"), None)
    finally:
        parent_ledger.close()
    if not parent or not parent.get("checkpoint_manifest"):
        raise ValueError("temporal research requires a succeeded EXP-004A parent")
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir); ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(evidence_id="KB-007", title="Inference-known weekday cross", source="Interpretation - temporal candidate from timestamp metadata", claim="A calendar field can interact with candidate features without relying on feedback labels.", assumptions=("calendar time is available before exposure",), operator_families=(OperatorFamily.TEMPORAL_HISTORY,), applicability="BPR temporal robustness candidate.", risks=("time effects may not generalize across the evaluation horizon",))])
    context = PlannerContext(goal="Test a day-of-week candidate cross without using any post-exposure outcome.", experiment_ids=("EXP-008",), run_class=RunClass.RESEARCH, parent_run_id=parent["run_id"], parent_checkpoint_sha256=parent["checkpoint_manifest"]["checkpoint_sha256"], allowed_operator_families=(OperatorFamily.TEMPORAL_HISTORY,), allowed_paths=(), token_budget=0, compute_budget_seconds=1800)
    planner = FixedPlanner({"rationale": "Keep the BPR model fixed and add one calendar field known at impression time.", "candidates": [{"experiment_id": "EXP-008", "operator_family": "temporal_history", "hypothesis": "An inference-known weekday cross improves temporal robustness of BPR.", "expected_mechanism": "weekday interacts with candidate fields to model repeatable time-dependent preferences.", "evidence_ids": ["KB-007"], "configuration": {"objective": "bpr", "temporal_day_cross": True, "seeds": [0, 1, 2, 3, 4]}, "controlled_variables": ["BPR loss", "FM optimizer", "seed set", "train/validation split"]}]})
    plan = planner.plan(context, knowledge); controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_ranking_candidate(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records: ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": controller.observe_for_convergence(records), "runs": [record.run_id for record in records]}
    ledger.close(); return response


def run_autonomous_three_ensemble(
    *, repository_root: str | Path, starter_kit_dir: str | Path, data_dir: str | Path,
    bpr_ledger_path: str | Path, history_ledger_path: str | Path, temporal_ledger_path: str | Path, output_dir: str | Path,
) -> dict[str, object]:
    """Evaluate a declared three-way rank blend from frozen component manifests."""
    paths = ((bpr_ledger_path, "EXP-004A"), (history_ledger_path, "EXP-005"), (temporal_ledger_path, "EXP-008"))
    parents = []
    for path, experiment_id in paths:
        source = ExperimentLedger(path)
        try: record = next((run for run in source.list_runs() if run["experiment_id"] == experiment_id and run["status"] == "succeeded"), None)
        finally: source.close()
        if not record or not record.get("checkpoint_manifest"): raise ValueError(f"three-way ensemble requires {experiment_id} manifest")
        parents.append(record)
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir); ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(evidence_id="KB-008", title="Three-source rank ensemble", source="Interpretation - frozen BPR, history, and temporal prediction blend", claim="A third temporal component may correct errors that remain after a BPR/history blend.", assumptions=("all components are immutable and prediction-aligned",), operator_families=(OperatorFamily.ENSEMBLE,), applicability="Frozen ensemble extension.", risks=("larger validation grid increases selection bias",))])
    context = PlannerContext(goal="Evaluate a small declared three-way rank ensemble grid from frozen components.", experiment_ids=("EXP-009A",), run_class=RunClass.RESEARCH, parent_run_id=parents[0]["run_id"], parent_checkpoint_sha256=parents[0]["checkpoint_manifest"]["checkpoint_sha256"], allowed_operator_families=(OperatorFamily.ENSEMBLE,), allowed_paths=(), token_budget=0, compute_budget_seconds=600)
    components = [{"ledger": str(path), "experiment_id": experiment_id} for path, experiment_id in paths]
    grid = [[0.375, 0.375, 0.25], [0.25, 0.5, 0.25], [0.25, 0.375, 0.375], [0.5, 0.25, 0.25]]
    planner = FixedPlanner({"rationale": "Blend only frozen predictions using a compact declared three-way grid; no component retraining.", "candidates": [{"experiment_id": "EXP-009A", "operator_family": "ensemble", "hypothesis": "A three-way rank blend improves primary validation score beyond the current two-way ensemble.", "expected_mechanism": "the temporal component contributes non-overlapping within-user ordering signal.", "evidence_ids": ["KB-008"], "configuration": {"components": components, "weight_grid": grid, "seeds": [0, 1, 2, 3, 4]}, "controlled_variables": ["frozen components", "validation rows", "seed set"]}]})
    plan = planner.plan(context, knowledge); controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_three_rank_ensemble(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records: ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": controller.observe_for_convergence(records), "runs": [record.run_id for record in records]}
    ledger.close(); return response


def run_autonomous_ensemble_confirmation(
    *, repository_root: str | Path, starter_kit_dir: str | Path, data_dir: str | Path,
    leader_ledger_path: str | Path, bpr_ledger_path: str | Path, history_ledger_path: str | Path,
    temporal_ledger_path: str | Path, output_dir: str | Path,
) -> dict[str, object]:
    """Run three predeclared, single-vector checks around a frozen ensemble leader.

    These are sequential campaign confirmations, not a new weight search: each
    batch contains exactly one predeclared vector and uses the exact immutable
    components of EXP-009A.  This provides honest post-leader convergence
    evidence without retraining components or inspecting test labels.
    """
    leader_experiment_id = "EXP-009E"
    source = ExperimentLedger(leader_ledger_path)
    try:
        leader = next((run for run in source.list_runs() if run["experiment_id"] == leader_experiment_id and run["status"] == "succeeded"), None)
    finally:
        source.close()
    if not leader or not leader.get("checkpoint_manifest"):
        raise ValueError(f"ensemble confirmation requires a succeeded {leader_experiment_id} leader manifest")
    leader_manifest = leader["checkpoint_manifest"]
    try:
        parent_ensemble = json.loads(Path(leader_manifest["checkpoint_path"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"ensemble confirmation cannot read the frozen {leader_experiment_id} artifact") from error
    component_refs = [
        {"ledger": str(bpr_ledger_path), "experiment_id": "EXP-004A"},
        {"ledger": str(history_ledger_path), "experiment_id": "EXP-005"},
        {"ledger": str(temporal_ledger_path), "experiment_id": "EXP-008"},
    ]
    parent_hashes = [component.get("checkpoint_sha256") for component in parent_ensemble.get("components", [])]
    resolved_hashes: list[str] = []
    for component in component_refs:
        component_ledger = ExperimentLedger(component["ledger"])
        try:
            record = next((run for run in component_ledger.list_runs() if run["experiment_id"] == component["experiment_id"] and run["status"] == "succeeded"), None)
        finally:
            component_ledger.close()
        if not record or not record.get("checkpoint_manifest"):
            raise ValueError(f"ensemble confirmation component {component['experiment_id']} is unavailable")
        resolved_hashes.append(str(record["checkpoint_manifest"]["checkpoint_sha256"]))
    if parent_hashes != resolved_hashes:
        raise ValueError(f"ensemble confirmation components do not match the frozen {leader_experiment_id} leader")
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir)
    ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(
        evidence_id="KB-014", title="Frozen ensemble local sensitivity confirmation",
        source="Interpretation - predeclared local checks around the measured EXP-009A rank blend",
        claim="Fixed alternative component weights can confirm whether the frozen ensemble's result is sensitive to a small, documented weight perturbation.",
        assumptions=("all component checkpoints and seed predictions remain immutable",),
        operator_families=(OperatorFamily.ENSEMBLE,), applicability="Post-leader campaign confirmation only.",
        risks=("validation feedback can overfit if vectors are not predeclared and fully recorded",),
    )])
    confirmations = (
        ("EXP-009F", [0.50, 0.375, 0.125], "more BPR mass"),
        ("EXP-009G", [0.25, 0.625, 0.125], "more history mass"),
        ("EXP-009H", [0.25, 0.25, 0.50], "more temporal mass"),
    )
    controller = ResearchController(benchmark, ledger)
    records = []
    for experiment_id, vector, rationale_suffix in confirmations:
        context = PlannerContext(
            goal=f"Confirm the frozen {leader_experiment_id} ensemble with one predeclared vector using {rationale_suffix}.",
            experiment_ids=(experiment_id,), run_class=RunClass.RESEARCH,
            parent_run_id=leader["run_id"], parent_checkpoint_sha256=leader_manifest["checkpoint_sha256"],
            allowed_operator_families=(OperatorFamily.ENSEMBLE,), allowed_paths=(), token_budget=0, compute_budget_seconds=600,
        )
        planner = FixedPlanner({"rationale": f"Evaluate exactly one frozen-component vector ({rationale_suffix}); do not search weights or retrain.", "candidates": [{
            "experiment_id": experiment_id, "operator_family": "ensemble",
            "hypothesis": f"The frozen {leader_experiment_id} component blend remains robust under the predeclared {rationale_suffix} perturbation.",
            "expected_mechanism": "a fixed alternative rank-space weighting exposes sensitivity without changing components or data.",
            "evidence_ids": ["KB-014"],
            "configuration": {"components": component_refs, "weight_grid": [vector], "seeds": [0, 1, 2, 3, 4]},
            "controlled_variables": ["frozen component checkpoints", "validation rows", "seed set", "single declared vector"],
        }]})
        plan = planner.plan(context, knowledge)
        batch_records = controller.execute_batch(plan.batch, lambda candidate: execute_three_rank_ensemble(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
        for record in batch_records:
            ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
        records.extend(batch_records)
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": controller.observe_for_convergence(records), "runs": [record.run_id for record in records]}
    ledger.close(); return response


def run_autonomous_ensemble_revalidation(
    *, repository_root: str | Path, starter_kit_dir: str | Path, data_dir: str | Path,
    source_leader_ledger_path: str | Path, bpr_ledger_path: str | Path, history_ledger_path: str | Path,
    temporal_ledger_path: str | Path, output_dir: str | Path,
) -> dict[str, object]:
    """Revalidate EXP-009A's exact frozen vector under the current data identity."""
    source = ExperimentLedger(source_leader_ledger_path)
    try:
        prior = next((run for run in source.list_runs() if run["experiment_id"] == "EXP-009A" and run["status"] == "succeeded"), None)
    finally:
        source.close()
    if not prior or not prior.get("checkpoint_manifest"):
        raise ValueError("ensemble revalidation requires the historical EXP-009A manifest")
    try:
        prior_ensemble = json.loads(Path(prior["checkpoint_manifest"]["checkpoint_path"]).read_text(encoding="utf-8"))
        vector = prior_ensemble["component_weights"]
    except (OSError, json.JSONDecodeError, KeyError) as error:
        raise ValueError("ensemble revalidation cannot read the historical EXP-009A vector") from error
    if not isinstance(vector, list) or len(vector) != 3:
        raise ValueError("historical EXP-009A vector is invalid")
    component_refs = [
        {"ledger": str(bpr_ledger_path), "experiment_id": "EXP-004A"},
        {"ledger": str(history_ledger_path), "experiment_id": "EXP-005"},
        {"ledger": str(temporal_ledger_path), "experiment_id": "EXP-008"},
    ]
    prior_hashes = [component.get("checkpoint_sha256") for component in prior_ensemble.get("components", [])]
    current_hashes: list[str] = []
    for component in component_refs:
        component_ledger = ExperimentLedger(component["ledger"])
        try:
            record = next((run for run in component_ledger.list_runs() if run["experiment_id"] == component["experiment_id"] and run["status"] == "succeeded"), None)
        finally:
            component_ledger.close()
        if not record or not record.get("checkpoint_manifest"):
            raise ValueError(f"ensemble revalidation component {component['experiment_id']} is unavailable")
        current_hashes.append(str(record["checkpoint_manifest"]["checkpoint_sha256"]))
    if prior_hashes != current_hashes:
        raise ValueError("historical EXP-009A component identities no longer match")
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir); ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(
        evidence_id="KB-015", title="Frozen ensemble data-identity revalidation",
        source="Interpretation - remeasurement required after a campaign data-fingerprint mismatch",
        claim="A frozen score blend must be remeasured under one data fingerprint before it can anchor a campaign.",
        assumptions=("component checkpoint hashes match the historical blend",), operator_families=(OperatorFamily.ENSEMBLE,),
        applicability="Data-identity repair before provisional campaign construction.",
        risks=("the historical and current results may differ; no value is silently reused",),
    )])
    context = PlannerContext(
        goal="Revalidate the exact frozen EXP-009A component vector under the current KuaiRand-Pure data identity.",
        experiment_ids=("EXP-009E",), run_class=RunClass.RESEARCH, parent_run_id=prior["run_id"],
        parent_checkpoint_sha256=prior["checkpoint_manifest"]["checkpoint_sha256"],
        allowed_operator_families=(OperatorFamily.ENSEMBLE,), allowed_paths=(), token_budget=0, compute_budget_seconds=600,
    )
    planner = FixedPlanner({"rationale": "Reuse exactly the historical EXP-009A frozen vector once, with component hashes checked, to establish one current data identity before campaign continuation.", "candidates": [{
        "experiment_id": "EXP-009E", "operator_family": "ensemble",
        "hypothesis": "The exact frozen EXP-009A vector can be remeasured with the current data fingerprint without changing components or weights.",
        "expected_mechanism": "identical immutable component predictions are rescored on one current validation-data identity.",
        "evidence_ids": ["KB-015"],
        "configuration": {"components": component_refs, "weight_grid": [vector], "seeds": [0, 1, 2, 3, 4]},
        "controlled_variables": ["frozen component checkpoints", "single historical vector", "validation rows", "seed set"],
    }]})
    plan = planner.plan(context, knowledge); controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_three_rank_ensemble(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records: ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": controller.observe_for_convergence(records), "runs": [record.run_id for record in records]}
    ledger.close(); return response


def run_autonomous_backbone(
    *, repository_root: str | Path, starter_kit_dir: str | Path, data_dir: str | Path,
    parent_ledger_path: str | Path, output_dir: str | Path,
) -> dict[str, object]:
    """Evaluate a compact nonlinear DeepFM BPR backbone from the BPR parent."""
    source = ExperimentLedger(parent_ledger_path)
    try: parent = next((run for run in source.list_runs() if run["experiment_id"] == "EXP-004A" and run["status"] == "succeeded"), None)
    finally: source.close()
    if not parent or not parent.get("checkpoint_manifest"): raise ValueError("backbone research requires a succeeded EXP-004A parent")
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = starter_kuairand_pure_spec(starter_kit_dir); ledger = ExperimentLedger(output_dir / "ledger.sqlite")
    knowledge = KnowledgeBase([EvidenceCard(evidence_id="KB-009", title="DeepFM nonlinear interactions", source="Guo et al. (2017), DeepFM", claim="A neural tower over field embeddings can model higher-order feature interactions alongside FM terms.", assumptions=("small architecture is trainable under the project compute budget",), operator_families=(OperatorFamily.BACKBONE,), applicability="Controlled BPR backbone replacement.", risks=("more capacity can overfit short temporal validation",))])
    context = PlannerContext(goal="Test whether a compact DeepFM tower improves BPR ranking beyond factorization-machine interactions.", experiment_ids=("EXP-012",), run_class=RunClass.RESEARCH, parent_run_id=parent["run_id"], parent_checkpoint_sha256=parent["checkpoint_manifest"]["checkpoint_sha256"], allowed_operator_families=(OperatorFamily.BACKBONE,), allowed_paths=(), token_budget=0, compute_budget_seconds=3600)
    planner = FixedPlanner({"rationale": "Replace only the FM backbone with a compact nonlinear tower while retaining BPR, fields, splits, and seeds.", "candidates": [{"experiment_id": "EXP-012", "operator_family": "backbone", "hypothesis": "DeepFM's nonlinear tower improves BPR validation primary.", "expected_mechanism": "higher-order interactions complement pairwise FM terms.", "evidence_ids": ["KB-009"], "configuration": {"objective": "bpr", "hidden": 64, "seeds": [0, 1, 2, 3, 4]}, "controlled_variables": ["BPR loss", "fields", "train/validation split", "seed set"]}]})
    plan = planner.plan(context, knowledge); controller = ResearchController(benchmark, ledger)
    records = controller.execute_batch(plan.batch, lambda candidate: execute_ranking_candidate(candidate, repository_root=repository_root, starter_kit_dir=starter_kit_dir, data_dir=data_dir, artifact_root=output_dir / "artifacts"))
    for record in records: ledger.append_event(record.run_id, "planner_decision", {"rationale": plan.rationale, "provider": "fixed_offline_policy"})
    snapshot = MemoryManager(ledger).consolidate(); report = write_report(ledger, output_dir / "report.md")
    response = {"ledger": str(output_dir / "ledger.sqlite"), "report": str(report), "memory_snapshot": snapshot["snapshot_id"], "converged": controller.observe_for_convergence(records), "runs": [record.run_id for record in records]}
    ledger.close(); return response

from __future__ import annotations

import unittest

from tiktok_ml_agent.contracts import EvidenceCard, OperatorFamily, RunClass
from tiktok_ml_agent.memory import KnowledgeBase
from tiktok_ml_agent.planner import FixedPlanner, PlannerContext, PlannerError


class PlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.knowledge = KnowledgeBase(
            [
                EvidenceCard(
                    evidence_id="KB-1",
                    title="ranking evidence",
                    source="test",
                    claim="same-user pairwise learning can align ranking",
                    assumptions=(),
                    operator_families=(OperatorFamily.LOSS_OBJECTIVE,),
                    applicability="test",
                )
            ]
        )
        self.context = PlannerContext(
            goal="test ranking objective",
            experiment_ids=("EXP-004", "EXP-005"),
            run_class=RunClass.RESEARCH,
            parent_run_id="parent",
            parent_checkpoint_sha256="abc",
            allowed_operator_families=(OperatorFamily.LOSS_OBJECTIVE,),
            allowed_paths=("src/tiktok_ml_agent/",),
            token_budget=300,
            compute_budget_seconds=60,
        )

    def test_fixed_planner_binds_siblings_to_parent(self) -> None:
        planner = FixedPlanner(
            {
                "rationale": "Compare two ranking objectives with identical controls.",
                "candidates": [
                    {
                        "experiment_id": "EXP-004",
                        "operator_family": "loss_objective",
                        "hypothesis": "BPR improves within-user ordering.",
                        "expected_mechanism": "positive impressions outrank negatives.",
                        "evidence_ids": ["KB-1"],
                        "configuration": {"objective": "bpr"},
                        "controlled_variables": ["FM backbone"],
                    }
                ],
            }
        )
        result = planner.plan(self.context, self.knowledge)
        candidate = result.batch.candidates[0]
        self.assertEqual(candidate.parent_run_id, "parent")
        self.assertEqual(candidate.parent_checkpoint_sha256, "abc")
        self.assertEqual(candidate.allowed_paths, ("src/tiktok_ml_agent/",))

    def test_planner_rejects_unapproved_operator(self) -> None:
        planner = FixedPlanner(
            {
                "rationale": "bad",
                "candidates": [
                    {
                        "experiment_id": "EXP-004",
                        "operator_family": "backbone",
                        "hypothesis": "bad",
                        "expected_mechanism": "bad",
                        "evidence_ids": ["KB-1"],
                        "configuration": {},
                        "controlled_variables": [],
                    }
                ],
            }
        )
        with self.assertRaises(PlannerError):
            planner.plan(self.context, self.knowledge)


if __name__ == "__main__":
    unittest.main()

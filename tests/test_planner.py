from __future__ import annotations

import unittest
import json
from unittest.mock import MagicMock, patch

from tiktok_ml_agent.contracts import EvidenceCard, OperatorFamily, RunClass
from tiktok_ml_agent.memory import KnowledgeBase
from tiktok_ml_agent.planner import FixedPlanner, OpenAIResponsesPlanner, PlannerContext, PlannerError


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
            experiment_ids=("EXP-004A", "EXP-004B"),
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
                        "experiment_id": "EXP-004A",
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
                        "experiment_id": "EXP-004A",
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

    def test_openai_planner_binds_usage_and_validates_the_response(self) -> None:
        proposal = {
            "rationale": "Use the approved objective family only.",
            "candidates": [
                {
                    "experiment_id": "EXP-004A",
                    "operator_family": "loss_objective",
                    "hypothesis": "BPR improves ranking.",
                    "expected_mechanism": "same-user positives outrank negatives.",
                    "evidence_ids": ["KB-1"],
                    "configuration": {"objective": "bpr"},
                    "controlled_variables": ["FM backbone"],
                }
            ],
        }
        response = MagicMock()
        response.read.return_value = json.dumps({
            "id": "resp-test", "output_text": json.dumps(proposal),
            "usage": {"input_tokens": 123, "output_tokens": 45},
        }).encode()
        manager = MagicMock(); manager.__enter__.return_value = response
        planner = OpenAIResponsesPlanner("test-model", api_key="test-key")
        with patch("tiktok_ml_agent.planner.urlopen", return_value=manager) as request_call:
            result = planner.plan(self.context, self.knowledge)
        self.assertEqual(result.provider_response_id, "resp-test")
        self.assertEqual((result.input_tokens, result.output_tokens), (123, 45))
        self.assertEqual(result.batch.candidates[0].experiment_id, "EXP-004A")
        request = request_call.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertNotIn("test-key", request.data.decode())


if __name__ == "__main__":
    unittest.main()

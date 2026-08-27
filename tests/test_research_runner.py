from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tiktok_ml_agent.contracts import ExperimentSpec, OperatorFamily, RunClass
from tiktok_ml_agent.research_runner import execute_ranking_candidate


class ResearchRunnerTests(unittest.TestCase):
    def test_invalid_objective_is_rejected_before_data_access(self) -> None:
        candidate = ExperimentSpec(
            experiment_id="EXP-004",
            run_class=RunClass.RESEARCH,
            operator_family=OperatorFamily.LOSS_OBJECTIVE,
            hypothesis="invalid configuration should fail safely",
            expected_mechanism="runner validates the bounded objective setting.",
            configuration={"objective": "not-an-objective"},
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                execute_ranking_candidate(
                    candidate,
                    repository_root=directory,
                    starter_kit_dir=Path(directory) / "missing-kit",
                    data_dir=Path(directory) / "missing-data",
                    artifact_root=Path(directory) / "artifacts",
                )


if __name__ == "__main__":
    unittest.main()

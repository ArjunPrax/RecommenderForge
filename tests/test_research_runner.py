from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

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

    def test_parent_prediction_audit_is_recorded(self) -> None:
        candidate = ExperimentSpec(
            experiment_id="EXP-005",
            run_class=RunClass.RESEARCH,
            operator_family=OperatorFamily.TEMPORAL_HISTORY,
            hypothesis="history crosses change ranking",
            expected_mechanism="candidate interactions alter at least one ranking.",
            configuration={"objective": "bpr", "seeds": [0]},
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent_prediction = root / "parent.validation.npy"
            np.save(parent_prediction, np.asarray([0.9, 0.1]))
            candidate = ExperimentSpec(
                experiment_id="EXP-005",
                run_class=RunClass.RESEARCH,
                operator_family=OperatorFamily.TEMPORAL_HISTORY,
                hypothesis="history crosses change ranking",
                expected_mechanism="candidate interactions alter at least one ranking.",
                configuration={"objective": "bpr", "seeds": [0], "parent_validation_prediction_path": str(parent_prediction)},
            )
            adapter = SimpleNamespace(
                data=SimpleNamespace(data_fingerprint=lambda: "data"),
                spec=SimpleNamespace(evaluator_sha256="evaluator"),
                development_rows=lambda split: [SimpleNamespace(user_id="u"), SimpleNamespace(user_id="u")],
            )

            def fake_run(*args, checkpoint_path, **kwargs):
                checkpoint = Path(checkpoint_path)
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                checkpoint.write_bytes(b"checkpoint")
                prediction = checkpoint.with_suffix(".validation.npy")
                np.save(prediction, np.asarray([0.1, 0.9]))
                return {"GAUC": 0.7, "nDCG@5": 0.6, "primary": 0.65, "seed": 0.0, "checkpoint_path": str(checkpoint), "checkpoint_sha256": "checkpoint", "validation_prediction_sha256": "prediction"}

            with patch("tiktok_ml_agent.research_runner.KuaiRandPureAdapter", return_value=adapter), patch(
                "tiktok_ml_agent.research_runner.run_ranking_fm", side_effect=fake_run
            ), patch("tiktok_ml_agent.research_runner._git_identity", return_value=("revision", "diff")):
                result = execute_ranking_candidate(
                    candidate, repository_root=root, starter_kit_dir=root, data_dir=root, artifact_root=root / "artifacts"
                )
            self.assertEqual(result.diagnosis["ordering_change_audit"]["changed_users"], 1)


if __name__ == "__main__":
    unittest.main()

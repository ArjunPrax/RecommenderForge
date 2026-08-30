from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tiktok_ml_agent.contracts import ExperimentSpec, OperatorFamily, RunClass
from tiktok_ml_agent.worktree_executor import WorktreeCommandExecutor


class WorktreeCommandExecutorTests(unittest.TestCase):
    def test_host_command_result_is_bound_to_candidate_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executor = WorktreeCommandExecutor(root, root / "artifacts", lambda worktree, candidate, result: ["true"])
            candidate = ExperimentSpec(
                experiment_id="EXP-099",
                run_class=RunClass.QUALIFICATION,
                operator_family=OperatorFamily.HYPERPARAMETER,
                hypothesis="worktree command fixture",
                expected_mechanism="a trusted command writes structured metrics.",
            )
            with patch("tiktok_ml_agent.worktree_executor.subprocess.run") as run, patch.object(
                executor.manager, "execute_candidate"
            ) as isolated:
                run.side_effect = [SimpleNamespace(stdout="revision\n"), SimpleNamespace(stdout="ok")]
                def call_action(run_id, revision, spec, action):
                    output = root / "artifacts" / "results" / f"{run_id}.json"
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(json.dumps({"metrics": {"primary": 0.6}}), encoding="utf-8")
                    return action(root)
                isolated.side_effect = call_action
                result = executor.execute("fixture", candidate)
            self.assertEqual(result.metrics["primary"], 0.6)
            isolated.assert_called_once()


if __name__ == "__main__":
    unittest.main()

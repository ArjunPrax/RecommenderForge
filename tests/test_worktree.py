from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tiktok_ml_agent.contracts import ExperimentSpec, OperatorFamily, RunClass
from tiktok_ml_agent.controller import ExecutionResult
from tiktok_ml_agent.worktree import GitWorktreeManager


class GitWorktreeManagerTests(unittest.TestCase):
    def test_safe_worktree_creation_invokes_detached_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = GitWorktreeManager(root, root / "artifacts" / "worktrees")
            with patch("tiktok_ml_agent.worktree.subprocess.run") as run:
                worktree = manager.create("exp-001-run", "abc123")
            self.assertEqual(worktree.parent_revision, "abc123")
            self.assertIn("worktree", run.call_args.args[0])

    def test_candidate_patch_is_checked_and_worktree_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = GitWorktreeManager(root, root / "artifacts" / "worktrees")
            candidate = ExperimentSpec(
                experiment_id="EXP-004",
                run_class=RunClass.RESEARCH,
                operator_family=OperatorFamily.LOSS_OBJECTIVE,
                hypothesis="test patch isolation",
                expected_mechanism="test only",
                allowed_paths=("src/",),
                configuration={
                    "patch": "diff --git a/src/x.py b/src/x.py\nindex 1..2 100644\n--- a/src/x.py\n+++ b/src/x.py\n@@ -1 +1 @@\n-a\n+b\n"
                },
            )
            with patch.object(manager, "create", wraps=manager.create) as create, patch.object(manager, "remove") as remove, patch(
                "tiktok_ml_agent.worktree.subprocess.run"
            ) as run:
                # The isolated path does not need to exist because subprocess is mocked.
                create.return_value = type("Worktree", (), {"run_id": "r", "path": root, "parent_revision": "base"})()
                result = manager.execute_candidate(
                    "r", "base", candidate, lambda _: ExecutionResult(metrics={"primary": 1.0})
                )
            self.assertEqual(result.code_revision, "base")
            self.assertIsNotNone(result.diff_sha256)
            self.assertEqual(run.call_count, 2)
            remove.assert_called_once()
            with self.assertRaises(ValueError):
                manager.create("../../unsafe", "abc123")

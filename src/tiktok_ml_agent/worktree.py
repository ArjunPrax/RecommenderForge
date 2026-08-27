"""Git worktree lifecycle for isolated experiment candidates."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Callable, TYPE_CHECKING

from .patcher import validate_patch

if TYPE_CHECKING:
    from .contracts import ExperimentSpec
    from .controller import ExecutionResult


SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


@dataclass(frozen=True, slots=True)
class CandidateWorktree:
    run_id: str
    path: Path
    parent_revision: str


class GitWorktreeManager:
    def __init__(self, repository_root: str | Path, worktree_root: str | Path) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.worktree_root = Path(worktree_root).resolve()

    def create(self, run_id: str, parent_revision: str) -> CandidateWorktree:
        if not SAFE_ID.fullmatch(run_id):
            raise ValueError("run_id contains unsafe path characters")
        path = self.worktree_root / run_id
        if path.exists():
            raise FileExistsError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(path), parent_revision],
            cwd=self.repository_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return CandidateWorktree(run_id=run_id, path=path, parent_revision=parent_revision)

    def remove(self, worktree: CandidateWorktree) -> None:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree.path)],
            cwd=self.repository_root,
            check=True,
            capture_output=True,
            text=True,
        )

    def execute_candidate(
        self,
        run_id: str,
        parent_revision: str,
        candidate: "ExperimentSpec",
        action: Callable[[Path], "ExecutionResult"],
    ) -> "ExecutionResult":
        """Apply an approved candidate diff in a disposable worktree and execute it.

        The candidate has no shell capability: the host supplies `action` and
        determines the executable. A patch is retained by hash in the result
        before its worktree is forcibly removed.
        """
        worktree = self.create(run_id, parent_revision)
        patch = candidate.configuration.get("patch", "")
        if not isinstance(patch, str):
            self.remove(worktree)
            raise ValueError("candidate patch must be text")
        try:
            validate_patch(patch, candidate.allowed_paths)
            if patch:
                subprocess.run(
                    ["git", "apply", "--check", "-"],
                    cwd=worktree.path,
                    input=patch,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["git", "apply", "-"],
                    cwd=worktree.path,
                    input=patch,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            result = action(worktree.path)
            return replace(
                result,
                code_revision=parent_revision,
                diff_sha256=sha256(patch.encode()).hexdigest(),
            )
        finally:
            self.remove(worktree)

"""Run trusted host commands against candidate patches in disposable worktrees."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Callable

from .contracts import ExperimentSpec
from .controller import ExecutionResult
from .worktree import GitWorktreeManager


CommandFactory = Callable[[Path, ExperimentSpec, Path], list[str]]


@dataclass(slots=True)
class WorktreeCommandExecutor:
    """A host-owned command boundary; candidates never choose executable commands.

    A trusted command factory creates the argv and requires a JSON result file.
    The model/candidate may only supply a patch subject to `allowed_paths`.
    """

    repository_root: Path
    artifact_root: Path
    command_factory: CommandFactory
    manager: GitWorktreeManager = field(init=False)

    def __post_init__(self) -> None:
        self.repository_root = self.repository_root.resolve()
        self.artifact_root = self.artifact_root.resolve()
        self.manager = GitWorktreeManager(self.repository_root, self.artifact_root / "worktrees")

    def execute(self, run_id: str, candidate: ExperimentSpec) -> ExecutionResult:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.repository_root, check=True, capture_output=True, text=True
        ).stdout.strip()
        result_path = self.artifact_root / "results" / f"{run_id}.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)

        def action(worktree: Path) -> ExecutionResult:
            started = perf_counter()
            command = self.command_factory(worktree, candidate, result_path)
            completed = subprocess.run(command, cwd=worktree, check=True, capture_output=True, text=True)
            if not result_path.is_file():
                raise RuntimeError("trusted candidate command did not produce its required result JSON")
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            metrics = payload.get("metrics")
            if not isinstance(metrics, dict) or not all(isinstance(value, (float, int)) for value in metrics.values()):
                raise ValueError("candidate result JSON requires numeric metrics")
            return ExecutionResult(
                metrics={str(key): float(value) for key, value in metrics.items()},
                diagnosis={"stdout": completed.stdout[-4000:], **dict(payload.get("diagnosis", {}))},
                resource_usage={"cpu_seconds": perf_counter() - started, **dict(payload.get("resource_usage", {}))},
            )

        return self.manager.execute_candidate(run_id, revision, candidate, action)

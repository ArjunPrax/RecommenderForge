"""Deterministic candidate execution, recovery, and convergence."""

from __future__ import annotations

from dataclasses import dataclass, field
from contextlib import contextmanager
from hashlib import sha256
import signal
import threading
from time import perf_counter
from typing import Callable, Iterable, Protocol
from uuid import uuid4

from .contracts import (
    BenchmarkSpec,
    CheckpointManifest,
    ExperimentSpec,
    RunClass,
    RunRecord,
    RunStatus,
)
from .ledger import ExperimentLedger


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    metrics: dict[str, float]
    diagnosis: dict[str, object] = field(default_factory=dict)
    checkpoint_manifest: CheckpointManifest | None = None
    resource_usage: dict[str, float] = field(default_factory=dict)
    code_revision: str | None = None
    diff_sha256: str | None = None
    data_fingerprint: str | None = None
    evaluator_sha256: str | None = None
    seeds: tuple[int, ...] = ()
    interventions: int = 0


@dataclass(frozen=True, slots=True)
class CandidateBatch:
    batch_id: str
    parent_run_id: str | None
    parent_checkpoint_sha256: str | None
    candidates: tuple[ExperimentSpec, ...]

    def __post_init__(self) -> None:
        if not 1 <= len(self.candidates) <= 3:
            raise ValueError("candidate batches must contain one to three siblings")
        for candidate in self.candidates:
            if candidate.parent_run_id != self.parent_run_id:
                raise ValueError("all candidate siblings must share the immutable parent run")
            if candidate.parent_checkpoint_sha256 != self.parent_checkpoint_sha256:
                raise ValueError("all candidate siblings must share the immutable parent checkpoint")


@dataclass(slots=True)
class ConvergenceTracker:
    epsilon: float
    patience: int
    best_score: float = float("-inf")
    best_run_id: str | None = None
    significant_anchor: float = float("-inf")
    stagnation: int = 0

    def observe(self, run_id: str, primary: float, eligible: bool = True) -> bool:
        if not eligible:
            return False
        if primary > self.best_score:
            self.best_score, self.best_run_id = primary, run_id
        if primary > self.significant_anchor + self.epsilon:
            self.significant_anchor = primary
            self.stagnation = 0
        else:
            self.stagnation += 1
        return self.stagnation >= self.patience


class RecoveryPolicy:
    @staticmethod
    def action_for(error: Exception) -> str:
        if isinstance(error, TimeoutError):
            return "terminate_stalled_candidate_and_return_to_parent"
        if isinstance(error, MemoryError):
            return "record_memory_failure_and_require_approved_scale_adjustment"
        if isinstance(error, FloatingPointError):
            return "record_numerical_failure_and_retry_once_with_safe_numerics"
        return "revert_candidate_worktree_to_immutable_parent"


Executor = Callable[[ExperimentSpec], ExecutionResult]


@contextmanager
def _candidate_wall_clock_limit(seconds: int | None):
    """Interrupt a budgeted candidate on the main POSIX thread.

    The planner supplies a wall-clock budget for every real research batch.
    An expired budget fails as a normal ``TimeoutError`` so the controller
    records its recovery action and continues with later sibling candidates.
    Qualification and unit callers without a budget remain deterministic.
    """
    if seconds is None:
        yield
        return
    if seconds <= 0:
        raise TimeoutError("candidate compute budget was exhausted before execution")
    if threading.current_thread() is not threading.main_thread() or not hasattr(signal, "setitimer"):
        # Threaded/non-POSIX hosts retain accounting and exception recovery,
        # but cannot safely install a process-global signal handler here.
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)

    def _raise_timeout(_signum: int, _frame: object) -> None:
        raise TimeoutError(f"candidate exceeded its {seconds}-second compute budget")

    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
        signal.signal(signal.SIGALRM, previous_handler)


class RunAwareExecutor(Protocol):
    """Executor variant that needs the ledger run ID for isolated artifacts."""

    def execute(self, run_id: str, candidate: ExperimentSpec) -> ExecutionResult: ...


class ResearchController:
    def __init__(self, benchmark: BenchmarkSpec, ledger: ExperimentLedger) -> None:
        self.benchmark = benchmark
        self.ledger = ledger
        self.convergence = ConvergenceTracker(benchmark.epsilon, benchmark.patience)

    def execute_batch(self, batch: CandidateBatch, executor: Executor) -> list[RunRecord]:
        records: list[RunRecord] = []
        for candidate in batch.candidates:
            run_id = f"{candidate.experiment_id.lower()}-{uuid4().hex[:12]}"
            record = RunRecord(
                run_id=run_id,
                experiment_id=candidate.experiment_id,
                run_class=candidate.run_class,
                status=RunStatus.RUNNING,
                benchmark_id=self.benchmark.benchmark_id,
                operator_family=candidate.operator_family,
                hypothesis=candidate.hypothesis,
                parent_run_id=batch.parent_run_id,
                configuration_sha256=sha256(repr(sorted(candidate.configuration.items())).encode()).hexdigest(),
            )
            self.ledger.create_run(record)
            self.ledger.append_event(
                run_id,
                "candidate_started",
                {"batch_id": batch.batch_id, "experiment": candidate.to_dict()},
            )
            started = perf_counter()
            try:
                with _candidate_wall_clock_limit(candidate.compute_budget_seconds):
                    if hasattr(executor, "execute"):
                        result = executor.execute(run_id, candidate)  # type: ignore[union-attr]
                    else:
                        result = executor(candidate)
                record.status = RunStatus.SUCCEEDED
                record.metrics = result.metrics
                record.diagnosis = result.diagnosis
                record.checkpoint_manifest = (
                    result.checkpoint_manifest.to_dict() if result.checkpoint_manifest else None
                )
                record.resource_usage = dict(result.resource_usage)
                record.resource_usage.setdefault("wall_seconds", perf_counter() - started)
                record.code_revision = result.code_revision
                record.diff_sha256 = result.diff_sha256
                record.data_fingerprint = result.data_fingerprint
                record.evaluator_sha256 = result.evaluator_sha256
                record.seeds = list(result.seeds)
                record.interventions = result.interventions
                self.ledger.append_event(run_id, "candidate_succeeded", {"metrics": result.metrics})
            except Exception as error:  # evidence must include controlled failures
                record.status = RunStatus.RECOVERED
                record.error = f"{type(error).__name__}: {error}"
                record.recovery = RecoveryPolicy.action_for(error)
                record.resource_usage["wall_seconds"] = perf_counter() - started
                if candidate.compute_budget_seconds is not None:
                    record.diagnosis["compute_budget_seconds"] = candidate.compute_budget_seconds
                self.ledger.append_event(
                    run_id,
                    "candidate_recovered",
                    {"error": record.error, "recovery": record.recovery},
                )
            self.ledger.finalize_run(record)
            records.append(record)
        return records

    def observe_for_convergence(self, records: Iterable[RunRecord]) -> bool:
        converged = False
        for record in records:
            eligible = (
                record.status is RunStatus.SUCCEEDED
                and record.run_class in {RunClass.RESEARCH, RunClass.DESIGNATED_FINAL}
                and "primary" in record.metrics
            )
            if eligible:
                converged = self.convergence.observe(record.run_id, record.metrics["primary"], True) or converged
        return converged

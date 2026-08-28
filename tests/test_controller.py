from __future__ import annotations

import tempfile
import signal
import time
import unittest
from pathlib import Path

from tiktok_ml_agent.contracts import BenchmarkSpec, ExperimentSpec, OperatorFamily, RunClass
from tiktok_ml_agent.controller import CandidateBatch, ExecutionResult, ResearchController
from tiktok_ml_agent.ledger import ExperimentLedger


class ControllerTests(unittest.TestCase):
    def test_siblings_share_parent_and_failures_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = ExperimentLedger(Path(directory) / "ledger.sqlite")
            spec = BenchmarkSpec("fixture", "v1", "label", ("primary",))
            controller = ResearchController(spec, ledger)
            candidates = (
                ExperimentSpec(
                    "EXP-003", RunClass.QUALIFICATION, OperatorFamily.HYPERPARAMETER,
                    "works", "returns a metric", configuration={"primary": 0.6},
                ),
                ExperimentSpec(
                    "EXP-003", RunClass.QUALIFICATION, OperatorFamily.HYPERPARAMETER,
                    "fails", "tests recovery", configuration={"fail": True},
                ),
            )
            batch = CandidateBatch("batch", None, None, candidates)

            def executor(candidate):
                if candidate.configuration.get("fail"):
                    raise RuntimeError("controlled")
                return ExecutionResult(metrics={"primary": candidate.configuration["primary"]})

            records = controller.execute_batch(batch, executor)
            self.assertEqual([record.parent_run_id for record in records], [None, None])
            self.assertEqual(records[0].status.value, "succeeded")
            self.assertEqual(records[1].status.value, "recovered")
            self.assertFalse(controller.observe_for_convergence(records))
            self.assertEqual(len(ledger.events_for(records[1].run_id)), 2)
            ledger.close()

    def test_run_aware_executor_receives_ledger_run_id(self) -> None:
        class Executor:
            seen: tuple[str, str] | None = None

            def execute(self, run_id, candidate):
                self.seen = (run_id, candidate.experiment_id)
                return ExecutionResult(metrics={"primary": 0.6})

        with tempfile.TemporaryDirectory() as directory:
            ledger = ExperimentLedger(Path(directory) / "ledger.sqlite")
            controller = ResearchController(BenchmarkSpec("fixture", "v1", "label", ("primary",)), ledger)
            candidate = ExperimentSpec("EXP-003", RunClass.QUALIFICATION, OperatorFamily.HYPERPARAMETER, "runs", "records its id")
            executor = Executor()
            record = controller.execute_batch(CandidateBatch("batch", None, None, (candidate,)), executor)[0]
            self.assertEqual(executor.seen, (record.run_id, "EXP-003"))
            ledger.close()

    def test_exhausted_budget_recovers_without_invoking_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = ExperimentLedger(Path(directory) / "ledger.sqlite")
            controller = ResearchController(BenchmarkSpec("fixture", "v1", "label", ("primary",)), ledger)
            candidate = ExperimentSpec(
                "EXP-003", RunClass.QUALIFICATION, OperatorFamily.HYPERPARAMETER,
                "times out", "deadline stops execution", compute_budget_seconds=0,
            )
            invoked = False

            def executor(_candidate):
                nonlocal invoked
                invoked = True
                return ExecutionResult(metrics={"primary": 0.6})

            record = controller.execute_batch(CandidateBatch("batch", None, None, (candidate,)), executor)[0]
            self.assertFalse(invoked)
            self.assertEqual(record.status.value, "recovered")
            self.assertEqual(record.recovery, "terminate_stalled_candidate_and_return_to_parent")
            self.assertEqual(record.diagnosis["compute_budget_seconds"], 0)
            ledger.close()

    @unittest.skipUnless(hasattr(signal, "setitimer"), "requires POSIX interval timers")
    def test_wall_clock_budget_interrupts_running_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = ExperimentLedger(Path(directory) / "ledger.sqlite")
            controller = ResearchController(BenchmarkSpec("fixture", "v1", "label", ("primary",)), ledger)
            candidate = ExperimentSpec(
                "EXP-003", RunClass.QUALIFICATION, OperatorFamily.HYPERPARAMETER,
                "times out", "wall-clock deadline interrupts execution", compute_budget_seconds=1,
            )

            def executor(_candidate):
                time.sleep(2)
                return ExecutionResult(metrics={"primary": 0.6})

            started = time.monotonic()
            record = controller.execute_batch(CandidateBatch("batch", None, None, (candidate,)), executor)[0]
            self.assertLess(time.monotonic() - started, 1.5)
            self.assertEqual(record.status.value, "recovered")
            self.assertIn("TimeoutError", record.error or "")
            self.assertEqual(record.recovery, "terminate_stalled_candidate_and_return_to_parent")
            ledger.close()

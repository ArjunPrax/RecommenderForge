from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tiktok_ml_agent.contracts import OperatorFamily, RunClass, RunRecord, RunStatus
from tiktok_ml_agent.ledger import ExperimentLedger
from tiktok_ml_agent.memory import MemoryManager


class LedgerMemoryTests(unittest.TestCase):
    def test_terminal_records_are_immutable_and_memory_preserves_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = ExperimentLedger(Path(directory) / "ledger.sqlite")
            record = RunRecord(
                run_id="run-1",
                experiment_id="EXP-001",
                run_class=RunClass.RESEARCH,
                status=RunStatus.RUNNING,
                benchmark_id="fixture",
                operator_family=OperatorFamily.HYPERPARAMETER,
                hypothesis="fixture",
            )
            ledger.create_run(record)
            record.status = RunStatus.SUCCEEDED
            record.metrics = {"primary": 0.61}
            ledger.finalize_run(record)
            with self.assertRaises(ValueError):
                ledger.finalize_run(record)
            manager = MemoryManager(ledger)
            snapshot = manager.consolidate()
            self.assertEqual(snapshot["source_run_count"], 1)
            self.assertEqual(snapshot["payload"]["source_run_ids"], ["run-1"])
            ledger.close()

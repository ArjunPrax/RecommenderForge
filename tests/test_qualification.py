from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tiktok_ml_agent.ledger import ExperimentLedger
from tiktok_ml_agent.qualification import run_qualification


class QualificationTests(unittest.TestCase):
    def test_qualification_produces_evidence_without_competition_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_qualification(Path(directory))
            self.assertTrue(result["converged"])
            self.assertEqual(result["memory_snapshot"], 1)
            report = Path(str(result["report"])).read_text(encoding="utf-8")
            self.assertIn("recovered", report)
            self.assertTrue(Path(str(result["submission"])).exists())
            ledger = ExperimentLedger(Path(str(result["ledger"])))
            events = [event for run in ledger.list_runs() for event in ledger.events_for(run["run_id"])]
            self.assertIn("candidate_recovered", [event["event_type"] for event in events])
            self.assertIn("test_access_denied", [event["event_type"] for event in events])
            ledger.close()

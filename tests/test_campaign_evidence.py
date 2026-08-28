from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tiktok_ml_agent.campaign import CampaignEvidenceError, evaluate_campaign, write_campaign_report
from tiktok_ml_agent.contracts import CheckpointManifest, OperatorFamily, RunClass, RunRecord, RunStatus, hash_file
from tiktok_ml_agent.finalization import designate_final
from tiktok_ml_agent.ledger import ExperimentLedger


def _ledger_with_run(path: Path, run_id: str, primary: float, *, evaluator: str = "evaluator-a") -> None:
    ledger = ExperimentLedger(path)
    record = RunRecord(
        run_id=run_id, experiment_id="EXP-900", run_class=RunClass.RESEARCH,
        status=RunStatus.RUNNING, benchmark_id="kuairand-pure",
        operator_family=OperatorFamily.HYPERPARAMETER, hypothesis="fixture",
    )
    ledger.create_run(record)
    record.status = RunStatus.SUCCEEDED
    record.metrics = {"primary": primary}
    record.evaluator_sha256 = evaluator
    record.resource_usage = {"cpu_seconds": 2.0}
    checkpoint = path.with_suffix(".checkpoint")
    checkpoint.write_bytes(run_id.encode())
    record.checkpoint_manifest = CheckpointManifest(
        checkpoint_path=str(checkpoint), checkpoint_sha256=hash_file(checkpoint), code_revision="fixture",
        data_fingerprint="fixture", evaluator_sha256=evaluator, configuration_sha256="config",
        validation_prediction_sha256="prediction", validation_metrics={"primary": primary},
    ).to_dict()
    ledger.finalize_run(record)
    ledger.close()


class CampaignEvidenceTests(unittest.TestCase):
    def test_declared_ledgers_produce_convergence_and_resource_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, score in enumerate((0.601, 0.6015, 0.6014), start=1):
                _ledger_with_run(root / f"run-{index}.sqlite", f"run-{index}", score)
            config = {
                "campaign_id": "fixture", "benchmark_id": "kuairand-pure", "baseline_primary": 0.60,
                "epsilon": 0.002, "patience": 3,
                "batches": [
                    {"batch_id": f"b{index}", "runs": [{"ledger": f"run-{index}.sqlite", "run_id": f"run-{index}"}]}
                    for index in range(1, 4)
                ],
            }
            config_path = root / "campaign.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            report = evaluate_campaign(config_path)
            self.assertTrue(report["converged"])
            self.assertEqual(report["best_run_id"], "run-2")
            self.assertEqual(report["resource_totals"], {"cpu_seconds": 6.0})
            output = write_campaign_report(config_path, root / "output.json")
            self.assertTrue(output.is_file())
            final = designate_final(campaign_report_path=output, final_ledger_path=root / "final.sqlite")
            final_ledger = ExperimentLedger(final["final_ledger"])
            final_record = final_ledger.get_run(final["final_run_id"])
            final_ledger.close()
            self.assertEqual(final_record["run_class"], "designated_final")
            self.assertEqual(final_record["parent_run_id"], "run-2")

    def test_mixed_evaluators_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _ledger_with_run(root / "one.sqlite", "one", 0.61, evaluator="one")
            _ledger_with_run(root / "two.sqlite", "two", 0.62, evaluator="two")
            config = {
                "campaign_id": "fixture", "benchmark_id": "kuairand-pure", "baseline_primary": 0.60,
                "batches": [{"batch_id": "b1", "runs": [{"ledger": "one.sqlite", "run_id": "one"}, {"ledger": "two.sqlite", "run_id": "two"}]}],
            }
            path = root / "campaign.json"; path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(CampaignEvidenceError):
                evaluate_campaign(path)


if __name__ == "__main__":
    unittest.main()

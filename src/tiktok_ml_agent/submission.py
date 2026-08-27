"""Generate a schema-valid output from a measured checkpoint, without retraining."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import torch

from .baseline_runner import encode_train_inference
from .contracts import CheckpointManifest, hash_file
from .history import prior_long_view_buckets
from .kuairand import KuaiRandPureAdapter
from .ledger import ExperimentLedger
from .multitask_fm import MultiTaskFM
from .torch_fm import TorchFM


def _manifest_from_ledger(path: str | Path, run_id: str) -> CheckpointManifest:
    ledger = ExperimentLedger(path)
    try:
        record = ledger.get_run(run_id)
    finally:
        ledger.close()
    manifest = record.get("checkpoint_manifest")
    if not manifest:
        raise ValueError("selected run has no frozen checkpoint manifest")
    return CheckpointManifest(**manifest)


def generate_submission(
    *, ledger_path: str | Path, run_id: str, starter_kit_dir: str | Path, data_dir: str | Path,
    output_path: str | Path,
) -> Path:
    """Generate and alignment-validate a CSV from the run's frozen checkpoint."""
    manifest = _manifest_from_ledger(ledger_path, run_id)
    checkpoint = Path(manifest.checkpoint_path)
    if not checkpoint.is_file() or hash_file(checkpoint) != manifest.checkpoint_sha256:
        raise ValueError("checkpoint is missing or no longer matches its frozen manifest")
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir)
    if adapter.spec.evaluator_sha256 != manifest.evaluator_sha256:
        raise ValueError("organizer evaluator changed since checkpoint validation")
    train = adapter.development_rows("train")
    test = adapter.submission_rows()
    state: dict[str, Any] = torch.load(checkpoint, map_location="cpu", weights_only=False)
    configuration = state.get("configuration", {})
    history_cross = bool(state.get("history_cross", False))
    if history_cross:
        train_history, test_history = prior_long_view_buckets(train, test)
        matrix, dimension = encode_train_inference(train, test, extra_train=train_history, extra_inference=test_history)
    else:
        matrix, dimension = encode_train_inference(train, test)
    state_dict = state["state_dict"]
    if "task_bias" in state_dict:
        model = MultiTaskFM(dimension, task_count=len(state_dict["task_bias"]), k=state_dict["V"].shape[1])
        predict = lambda tensor: model.task_logits(tensor, 0)
    else:
        model = TorchFM(dimension, k=state_dict["V"].shape[1])
        predict = model.logits
    model.load_state_dict(state_dict)
    with torch.no_grad():
        scores = predict(torch.from_numpy(matrix)).numpy()
    records = [(index, row.user_id, row.video_id, float(score)) for index, (row, score) in enumerate(zip(test, scores))]
    adapter.evaluator.validate_submission_rows([(row.user_id, row.video_id) for row in test], records)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(adapter.spec.submission_header)
        writer.writerows(records)
    return output_path

"""Validation-only rank ensemble over immutable component predictions."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import numpy as np

from .contracts import CheckpointManifest, ExperimentSpec, hash_file
from .controller import ExecutionResult
from .kuairand import KuaiRandPureAdapter
from .ledger import ExperimentLedger
from .research_runner import _git_identity


def _percentile_ranks(scores: np.ndarray) -> np.ndarray:
    order = np.argsort(scores, kind="stable")
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = np.arange(len(scores), dtype=np.float64)
    return ranks / max(1, len(scores) - 1)


def _component_manifest(ledger_path: str | Path, experiment_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    ledger = ExperimentLedger(ledger_path)
    try:
        record = next((run for run in ledger.list_runs() if run["experiment_id"] == experiment_id and run["status"] == "succeeded"), None)
    finally:
        ledger.close()
    if record is None or not record.get("checkpoint_manifest"):
        raise ValueError(f"ensemble component {experiment_id} has no succeeded checkpoint manifest")
    return record, record["checkpoint_manifest"]


def _prediction_paths(manifest: dict[str, Any], seeds: list[int]) -> list[Path]:
    best = Path(manifest["checkpoint_path"])
    paths = []
    for seed in seeds:
        path = best.parent / f"seed-{seed}.validation.npy"
        if not path.is_file():
            raise ValueError(f"component prediction is missing: {path}")
        paths.append(path)
    return paths


def execute_rank_ensemble(
    candidate: ExperimentSpec, *, repository_root: str | Path, starter_kit_dir: str | Path, data_dir: str | Path,
    artifact_root: str | Path,
) -> ExecutionResult:
    """Select a declared rank-blend weight using five-seed validation mean."""
    bpr_ledger = candidate.configuration.get("bpr_ledger")
    history_ledger = candidate.configuration.get("history_ledger")
    weights = candidate.configuration.get("bpr_weights", [0.25, 0.5, 0.75])
    seeds = candidate.configuration.get("seeds", [0, 1, 2, 3, 4])
    if not all(isinstance(value, (float, int)) and 0 <= value <= 1 for value in weights):
        raise ValueError("ensemble weights must be in [0, 1]")
    if not all(isinstance(seed, int) for seed in seeds):
        raise ValueError("ensemble seeds must be integers")
    bpr_record, bpr_manifest = _component_manifest(str(bpr_ledger), "EXP-004A")
    history_record, history_manifest = _component_manifest(str(history_ledger), "EXP-005")
    bpr_paths = _prediction_paths(bpr_manifest, seeds)
    history_paths = _prediction_paths(history_manifest, seeds)
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir)
    valid = adapter.development_rows("valid")
    users, labels = [row.user_id for row in valid], [int(row.label) for row in valid]
    evaluations: dict[float, list[dict[str, float]]] = {float(weight): [] for weight in weights}
    for weight in weights:
        for bpr_path, history_path in zip(bpr_paths, history_paths):
            bpr_scores, history_scores = np.load(bpr_path), np.load(history_path)
            scores = float(weight) * _percentile_ranks(bpr_scores) + (1 - float(weight)) * _percentile_ranks(history_scores)
            evaluations[float(weight)].append(adapter.evaluator.score_development("valid", users, labels, scores))
    selected_weight = max(weights, key=lambda weight: mean(entry["primary"] for entry in evaluations[float(weight)]))
    selected = evaluations[float(selected_weight)]
    metrics = {metric: mean(entry[metric] for entry in selected) for metric in ("GAUC", "nDCG@5", "primary")}
    metrics.update({f"{metric}_std": pstdev(entry[metric] for entry in selected) for metric in ("GAUC", "nDCG@5", "primary")})
    output = Path(artifact_root) / candidate.experiment_id.lower()
    output.mkdir(parents=True, exist_ok=True)
    best_seed_index = max(range(len(selected)), key=lambda index: selected[index]["primary"])
    best_prediction = float(selected_weight) * _percentile_ranks(np.load(bpr_paths[best_seed_index])) + (1 - float(selected_weight)) * _percentile_ranks(np.load(history_paths[best_seed_index]))
    prediction_path = output / "validation.npy"
    np.save(prediction_path, best_prediction)
    ensemble_path = output / "ensemble.json"
    ensemble = {
        "type": "global_percentile_rank_blend",
        "bpr_weight": float(selected_weight),
        "history_weight": 1 - float(selected_weight),
        "best_seed": seeds[best_seed_index],
        "components": [bpr_manifest, history_manifest],
        "weight_grid": list(weights),
        "all_weight_primary_means": {str(weight): mean(entry["primary"] for entry in results) for weight, results in evaluations.items()},
    }
    ensemble_path.write_text(json.dumps(ensemble, sort_keys=True, indent=2), encoding="utf-8")
    revision, diff = _git_identity(Path(repository_root))
    manifest = CheckpointManifest(
        checkpoint_path=str(ensemble_path), checkpoint_sha256=hash_file(ensemble_path), code_revision=revision,
        data_fingerprint=adapter.data.data_fingerprint(), evaluator_sha256=adapter.spec.evaluator_sha256,
        configuration_sha256=sha256(json.dumps(dict(candidate.configuration), sort_keys=True).encode()).hexdigest(),
        validation_prediction_sha256=hash_file(prediction_path), validation_metrics={key: float(value) for key, value in metrics.items() if not key.endswith("_std")},
    )
    return ExecutionResult(
        metrics=metrics, checkpoint_manifest=manifest, code_revision=revision, diff_sha256=diff,
        data_fingerprint=manifest.data_fingerprint, evaluator_sha256=manifest.evaluator_sha256, seeds=tuple(seeds),
        diagnosis={"summary": "Rank ensemble evaluated from frozen component prediction artifacts.", "selected_bpr_weight": float(selected_weight), "weight_primary_means": ensemble["all_weight_primary_means"], "component_runs": [bpr_record["run_id"], history_record["run_id"]]},
        resource_usage={"cpu_seconds": 0.0, "gpu_seconds": 0.0, "llm_input_tokens": 0.0, "llm_output_tokens": 0.0},
    )


def execute_three_rank_ensemble(
    candidate: ExperimentSpec, *, repository_root: str | Path, starter_kit_dir: str | Path, data_dir: str | Path,
    artifact_root: str | Path,
) -> ExecutionResult:
    """Evaluate a declared three-component rank blend, retaining every grid value."""
    raw_components = candidate.configuration.get("components")
    raw_weights = candidate.configuration.get("weight_grid")
    seeds = candidate.configuration.get("seeds", [0, 1, 2, 3, 4])
    if not isinstance(raw_components, list) or len(raw_components) != 3 or not isinstance(raw_weights, list):
        raise ValueError("three-way ensemble requires three components and a declared weight grid")
    if any(not isinstance(seed, int) for seed in seeds):
        raise ValueError("ensemble seeds must be integers")
    components: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for item in raw_components:
        if not isinstance(item, dict):
            raise ValueError("ensemble component specification must be an object")
        components.append(_component_manifest(item["ledger"], item["experiment_id"]))
    grids: list[tuple[float, float, float]] = []
    for item in raw_weights:
        if not isinstance(item, list) or len(item) != 3 or not all(isinstance(value, (int, float)) and value >= 0 for value in item):
            raise ValueError("each ensemble weight vector must contain three non-negative numbers")
        vector = tuple(float(value) for value in item)
        if not np.isclose(sum(vector), 1.0):
            raise ValueError("ensemble weights must sum to one")
        grids.append(vector)
    prediction_paths = [_prediction_paths(manifest, seeds) for _, manifest in components]
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir); valid = adapter.development_rows("valid")
    users, labels = [row.user_id for row in valid], [int(row.label) for row in valid]
    evaluations: dict[tuple[float, float, float], list[dict[str, float]]] = {vector: [] for vector in grids}
    for vector in grids:
        for index in range(len(seeds)):
            scores = sum(weight * _percentile_ranks(np.load(paths[index])) for weight, paths in zip(vector, prediction_paths))
            evaluations[vector].append(adapter.evaluator.score_development("valid", users, labels, scores))
    selected_vector = max(grids, key=lambda vector: mean(result["primary"] for result in evaluations[vector]))
    selected = evaluations[selected_vector]
    metrics = {metric: mean(result[metric] for result in selected) for metric in ("GAUC", "nDCG@5", "primary")}
    metrics.update({f"{metric}_std": pstdev(result[metric] for result in selected) for metric in ("GAUC", "nDCG@5", "primary")})
    best_seed_index = max(range(len(selected)), key=lambda index: selected[index]["primary"])
    best_prediction = sum(weight * _percentile_ranks(np.load(paths[best_seed_index])) for weight, paths in zip(selected_vector, prediction_paths))
    output = Path(artifact_root) / candidate.experiment_id.lower(); output.mkdir(parents=True, exist_ok=True)
    prediction_path = output / "validation.npy"; np.save(prediction_path, best_prediction)
    ensemble_path = output / "ensemble.json"
    ensemble = {"type": "global_percentile_rank_blend", "component_weights": list(selected_vector), "best_seed": seeds[best_seed_index], "components": [manifest for _, manifest in components], "weight_grid": [list(vector) for vector in grids], "all_weight_primary_means": {str(vector): mean(result["primary"] for result in evaluations[vector]) for vector in grids}}
    ensemble_path.write_text(json.dumps(ensemble, sort_keys=True, indent=2), encoding="utf-8")
    revision, diff = _git_identity(Path(repository_root))
    manifest = CheckpointManifest(checkpoint_path=str(ensemble_path), checkpoint_sha256=hash_file(ensemble_path), code_revision=revision, data_fingerprint=adapter.data.data_fingerprint(), evaluator_sha256=adapter.spec.evaluator_sha256, configuration_sha256=sha256(json.dumps(dict(candidate.configuration), sort_keys=True).encode()).hexdigest(), validation_prediction_sha256=hash_file(prediction_path), validation_metrics={key: float(value) for key, value in metrics.items() if not key.endswith("_std")})
    return ExecutionResult(metrics=metrics, checkpoint_manifest=manifest, code_revision=revision, diff_sha256=diff, data_fingerprint=manifest.data_fingerprint, evaluator_sha256=manifest.evaluator_sha256, seeds=tuple(seeds), diagnosis={"summary": "Three-component frozen rank ensemble evaluated over declared five-seed grid.", "selected_weights": list(selected_vector), "weight_primary_means": ensemble["all_weight_primary_means"], "component_runs": [record["run_id"] for record, _ in components]}, resource_usage={"cpu_seconds": 0.0, "gpu_seconds": 0.0, "llm_input_tokens": 0.0, "llm_output_tokens": 0.0})

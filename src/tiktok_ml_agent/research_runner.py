"""Candidate executor for checkpoint-backed, validation-only FM research."""

from __future__ import annotations

import json
import subprocess
from hashlib import sha256
from pathlib import Path
from statistics import mean, pstdev
from time import perf_counter
from typing import Iterable

import numpy as np

from .contracts import CheckpointManifest, ExperimentSpec, OperatorFamily
from .controller import ExecutionResult
from .kuairand import KuaiRandPureAdapter
from .multitask_fm import MultiTaskConfig, run_multitask_bpr
from .ordering import within_user_ordering_change
from .ranking_fm import RankingFMConfig, run_ranking_fm


def _git_identity(repository_root: Path) -> tuple[str, str]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository_root, check=True, capture_output=True, text=True
    ).stdout.strip()
    diff = subprocess.run(
        ["git", "diff", "--binary", "HEAD"], cwd=repository_root, check=True, capture_output=True, text=True
    ).stdout
    return revision, sha256(diff.encode()).hexdigest()


def _config_hash(configuration: object) -> str:
    return sha256(json.dumps(configuration, sort_keys=True, default=str).encode()).hexdigest()


def execute_ranking_candidate(
    candidate: ExperimentSpec,
    *,
    repository_root: str | Path,
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    artifact_root: str | Path,
) -> ExecutionResult:
    """Run a pre-approved objective over declared seeds and freeze its best seed.

    Candidate configurations are limited to ranking objective parameters.  This
    executor intentionally has no test split parameter and always derives all
    metrics through the adapter's validation-only path.
    """
    objective = candidate.configuration.get("objective")
    if objective not in {"bpr", "listwise"}:
        raise ValueError("ranking candidate must select bpr or listwise")
    raw_seeds = candidate.configuration.get("seeds", [0, 1, 2, 3, 4])
    if not isinstance(raw_seeds, list) or not raw_seeds or any(not isinstance(seed, int) for seed in raw_seeds):
        raise ValueError("candidate seeds must be a non-empty list of integers")
    common_config = {
        "k": int(candidate.configuration.get("k", 16)),
        "lr": float(candidate.configuration.get("lr", 0.001)),
        "epochs": int(candidate.configuration.get("epochs", 40)),
        "patience": int(candidate.configuration.get("patience", 4)),
    }
    config = RankingFMConfig(
        objective=str(objective), history_cross=bool(candidate.configuration.get("history_cross", False)),
        temporal_day_cross=bool(candidate.configuration.get("temporal_day_cross", False)), **common_config,
    )
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir)
    output_dir = Path(artifact_root) / candidate.experiment_id.lower() / f"{objective}-{_config_hash(candidate.configuration)[:12]}"
    output_dir.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    measurements: list[dict[str, float | str]] = []
    for seed in raw_seeds:
        checkpoint_path = output_dir / f"seed-{seed}.pt"
        if candidate.operator_family is OperatorFamily.MULTI_TASK:
            measurements.append(
                run_multitask_bpr(
                    starter_kit_dir,
                    data_dir,
                    seed,
                    MultiTaskConfig(auxiliary_weight=float(candidate.configuration.get("auxiliary_weight", 0.15)), **common_config),
                    checkpoint_path=checkpoint_path,
                )
            )
        else:
            measurements.append(run_ranking_fm(starter_kit_dir, data_dir, seed, config, checkpoint_path=checkpoint_path))
    metric_names = ("GAUC", "nDCG@5", "primary")
    metrics = {metric: mean(float(result[metric]) for result in measurements) for metric in metric_names}
    metrics.update({f"{metric}_std": pstdev(float(result[metric]) for result in measurements) for metric in metric_names})
    temporal_stability = {
        key: mean(float(result[key]) for result in measurements)
        for key in ("valid_early_primary", "valid_late_primary", "valid_temporal_gap")
        if key in measurements[0]
    }
    best = max(measurements, key=lambda result: float(result["primary"]))
    manifest = CheckpointManifest(
        checkpoint_path=str(best["checkpoint_path"]),
        checkpoint_sha256=str(best["checkpoint_sha256"]),
        code_revision=_git_identity(Path(repository_root))[0],
        data_fingerprint=adapter.data.data_fingerprint(),
        evaluator_sha256=adapter.spec.evaluator_sha256,
        configuration_sha256=_config_hash(candidate.configuration),
        validation_prediction_sha256=str(best["validation_prediction_sha256"]),
        validation_metrics={metric: float(best[metric]) for metric in metric_names},
    )
    ordering_audit: dict[str, int] | None = None
    parent_prediction_path = candidate.configuration.get("parent_validation_prediction_path")
    if parent_prediction_path is not None:
        parent_scores = np.load(Path(str(parent_prediction_path)))
        candidate_scores = np.load(Path(str(best["checkpoint_path"])).with_suffix(".validation.npy"))
        ordering_audit = within_user_ordering_change(
            [row.user_id for row in adapter.development_rows("valid")], parent_scores, candidate_scores
        )
        if ordering_audit["changed_users"] == 0:
            raise RuntimeError("candidate feature did not alter any within-user validation ordering")
    (output_dir / "measurements.json").write_text(json.dumps(measurements, indent=2, sort_keys=True), encoding="utf-8")
    revision, diff_sha = _git_identity(Path(repository_root))
    return ExecutionResult(
        metrics=metrics,
        diagnosis={
            "summary": f"{objective} was evaluated across {len(raw_seeds)} validation-only seeds.",
            "best_seed": int(float(best["seed"])),
            "best_seed_primary": float(best["primary"]),
            "selection_rule": "multi-seed mean ranks candidates; manifest freezes the best validation seed.",
            "ordering_change_audit": ordering_audit,
            "temporal_validation_stability": temporal_stability,
        },
        checkpoint_manifest=manifest,
        resource_usage={
            "cpu_seconds": perf_counter() - started,
            "gpu_seconds": 0.0,
            "llm_input_tokens": float(candidate.configuration.get("planner_input_tokens", 0)),
            "llm_output_tokens": float(candidate.configuration.get("planner_output_tokens", 0)),
        },
        code_revision=revision,
        diff_sha256=diff_sha,
        data_fingerprint=manifest.data_fingerprint,
        evaluator_sha256=manifest.evaluator_sha256,
        seeds=tuple(raw_seeds),
    )

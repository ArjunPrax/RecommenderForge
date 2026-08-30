"""Versioned contracts for autonomous benchmark research.

These types intentionally avoid model-framework dependencies. They are the
shared interface between the controller, model plugins, and judge-facing logs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


class RunClass(StrEnum):
    QUALIFICATION = "qualification"
    RESEARCH = "research"
    DESIGNATED_FINAL = "designated_final"


class RunStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RECOVERED = "recovered"
    REJECTED = "rejected"


class OperatorFamily(StrEnum):
    LOSS_OBJECTIVE = "loss_objective"
    SAMPLING = "sampling"
    CANDIDATE_CROSS = "candidate_cross"
    TEMPORAL_HISTORY = "temporal_history"
    MULTI_TASK = "multi_task"
    BACKBONE = "backbone"
    TRAINING_STRATEGY = "training_strategy"
    HYPERPARAMETER = "hyperparameter"
    ENSEMBLE = "ensemble"
    NOVEL = "novel"


class TestAccessError(PermissionError):
    """Raised when candidate-facing code requests prohibited hidden-test access."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def hash_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def primitive(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [primitive(item) for item in value]
    if isinstance(value, list):
        return [primitive(item) for item in value]
    if isinstance(value, dict):
        return {str(key): primitive(item) for key, item in value.items()}
    return value


@dataclass(frozen=True, slots=True)
class BenchmarkSpec:
    benchmark_id: str
    profile_id: str
    label: str
    metrics: tuple[str, ...]
    train_split: str = "train"
    validation_split: str = "valid"
    test_split: str = "test"
    evaluator_path: str | None = None
    evaluator_sha256: str | None = None
    epsilon: float = 0.002
    patience: int = 3
    submission_header: tuple[str, ...] = ("row_id", "user_id", "video_id", "score")
    source_note: str = ""

    def __post_init__(self) -> None:
        if self.epsilon < 0:
            raise ValueError("epsilon must be non-negative")
        if self.patience < 1:
            raise ValueError("patience must be at least one")
        if self.test_split in {self.train_split, self.validation_split}:
            raise ValueError("test split must be distinct from development splits")
        if self.evaluator_path and self.evaluator_sha256:
            actual = hash_file(self.evaluator_path)
            if actual != self.evaluator_sha256:
                raise ValueError("organizer evaluator hash does not match BenchmarkSpec")

    def assert_development_split(self, split: str) -> None:
        if split == self.test_split:
            raise TestAccessError(
                "hidden-test scoring is prohibited during development; generate output only"
            )
        if split not in {self.train_split, self.validation_split}:
            raise ValueError(f"unknown development split: {split}")

    def to_dict(self) -> dict[str, Any]:
        return primitive(asdict(self))


@dataclass(frozen=True, slots=True)
class EvidenceCard:
    evidence_id: str
    title: str
    source: str
    claim: str
    assumptions: tuple[str, ...]
    operator_families: tuple[OperatorFamily, ...]
    applicability: str
    risks: tuple[str, ...] = ()
    organizer_measured: bool = False

    def to_dict(self) -> dict[str, Any]:
        return primitive(asdict(self))


@dataclass(frozen=True, slots=True)
class ExperimentSpec:
    experiment_id: str
    run_class: RunClass
    operator_family: OperatorFamily
    hypothesis: str
    expected_mechanism: str
    parent_run_id: str | None = None
    parent_checkpoint_sha256: str | None = None
    evidence_ids: tuple[str, ...] = ()
    configuration: Mapping[str, Any] = field(default_factory=dict)
    controlled_variables: tuple[str, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    token_budget: int | None = None
    compute_budget_seconds: int | None = None

    def __post_init__(self) -> None:
        if not self.experiment_id.startswith("EXP-"):
            raise ValueError("experiment_id must use the EXP-XXX convention")
        if not self.hypothesis.strip() or not self.expected_mechanism.strip():
            raise ValueError("experiments require a hypothesis and expected mechanism")
        if self.operator_family is OperatorFamily.NOVEL and not self.evidence_ids:
            raise ValueError("novel operators require evidence or an explicit evidence record")

    def to_dict(self) -> dict[str, Any]:
        return primitive(asdict(self))


@dataclass(frozen=True, slots=True)
class CheckpointManifest:
    checkpoint_path: str
    checkpoint_sha256: str
    code_revision: str
    data_fingerprint: str
    evaluator_sha256: str | None
    configuration_sha256: str
    validation_prediction_sha256: str
    validation_metrics: Mapping[str, float]
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return primitive(asdict(self))


@dataclass(slots=True)
class RunRecord:
    run_id: str
    experiment_id: str
    run_class: RunClass
    status: RunStatus
    benchmark_id: str
    operator_family: OperatorFamily
    hypothesis: str
    parent_run_id: str | None = None
    code_revision: str | None = None
    diff_sha256: str | None = None
    data_fingerprint: str | None = None
    evaluator_sha256: str | None = None
    configuration_sha256: str | None = None
    seeds: list[int] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    checkpoint_manifest: dict[str, Any] | None = None
    diagnosis: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    recovery: str | None = None
    resource_usage: dict[str, float] = field(default_factory=dict)
    interventions: int = 0
    created_at: str = field(default_factory=utc_now)
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return primitive(asdict(self))

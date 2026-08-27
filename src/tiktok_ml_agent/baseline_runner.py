"""Safe reproduction runner for the organizer NumPy FM baseline.

It imports the organizer FM class but deliberately does not call `run_fm`, which
loads and scores the local test labels. Train/validation encoding is equivalent
to the starter kit because its vocabulary is built from training rows only.
"""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from .kuairand import KuaiRandPureAdapter, KuaiRandRow


@dataclass(frozen=True, slots=True)
class StarterFMConfig:
    k: int = 16
    lr: float = 0.001
    epochs: int = 40
    batch_size: int = 8192
    patience: int = 4


def _encode_train_validation(
    train: list[KuaiRandRow], valid: list[KuaiRandRow], *, extra_train: list[str] | None = None,
    extra_valid: list[str] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], int]:
    if (extra_train is None) != (extra_valid is None):
        raise ValueError("extra features must be provided for both train and validation")
    if extra_train is not None and (len(extra_train) != len(train) or len(extra_valid or []) != len(valid)):
        raise ValueError("extra feature lengths must match their row splits")
    durations = np.asarray([row.duration_ms for row in train])
    edges = np.quantile(durations, np.linspace(0, 1, 11)[1:-1])

    def raw(row: KuaiRandRow, extra: str | None) -> list[str]:
        values = [
            row.user_id,
            row.video_id,
            row.author_id,
            row.tab,
            str(int(np.searchsorted(edges, row.duration_ms))),
        ]
        if extra is not None:
            values.append(extra)
        return values

    vocabs = [dict() for _ in range(5 + int(extra_train is not None))]
    for row, extra in zip(train, extra_train or [None] * len(train)):
        for index, value in enumerate(raw(row, extra)):
            vocabs[index].setdefault(value, len(vocabs[index]))
    unknown = [len(vocab) for vocab in vocabs]
    field_dims = [len(vocab) + 1 for vocab in vocabs]
    offsets = np.cumsum([0, *field_dims[:-1]], dtype=np.int32)

    def encode(rows: list[KuaiRandRow], extras: list[str] | None) -> tuple[np.ndarray, np.ndarray, list[str]]:
        matrix = np.empty((len(rows), len(vocabs)), dtype=np.int32)
        labels = np.empty(len(rows), dtype=np.float32)
        users: list[str] = []
        for row_index, (row, extra) in enumerate(zip(rows, extras or [None] * len(rows))):
            if row.label is None:
                raise ValueError("baseline reproduction accepts development labels only")
            for field_index, value in enumerate(raw(row, extra)):
                matrix[row_index, field_index] = vocabs[field_index].get(value, unknown[field_index]) + offsets[field_index]
            labels[row_index] = row.label
            users.append(row.user_id)
        return matrix, labels, users

    x_train, y_train, _ = encode(train, extra_train)
    x_valid, y_valid, users_valid = encode(valid, extra_valid)
    return x_train, y_train, x_valid, y_valid, users_valid, int(sum(field_dims))


def encode_train_inference(
    train: list[KuaiRandRow], inference: list[KuaiRandRow], *, extra_train: list[str] | None = None,
    extra_inference: list[str] | None = None,
) -> tuple[np.ndarray, int]:
    """Fit vocabulary on labeled train rows and encode feature-only inference rows.

    The underlying encoder needs a label array for its development contract, so
    inference rows receive a fabricated zero solely for matrix allocation. The
    fabricated values are neither read from test data nor used by the returned
    feature matrix.
    """
    masked = [replace(row, label=0) for row in inference]
    _, _, encoded, _, _, dimension = _encode_train_validation(
        train, masked, extra_train=extra_train, extra_valid=extra_inference
    )
    return encoded, dimension


def _organizer_fm_class(starter_kit_dir: str | Path) -> type[Any]:
    kit = str(Path(starter_kit_dir).resolve())
    inserted = kit not in sys.path
    if inserted:
        sys.path.insert(0, kit)
    try:
        module = importlib.import_module("baseline")
        return module.FM
    finally:
        if inserted:
            sys.path.remove(kit)


def run_safe_numpy_fm(
    starter_kit_dir: str | Path,
    data_dir: str | Path,
    seed: int,
    config: StarterFMConfig | None = None,
) -> dict[str, float]:
    """Reproduce one organizer FM seed on train/valid only."""
    config = config or StarterFMConfig()
    adapter = KuaiRandPureAdapter(starter_kit_dir, data_dir)
    train = adapter.development_rows("train")
    valid = adapter.development_rows("valid")
    x_train, y_train, x_valid, _, users_valid, dimension = _encode_train_validation(train, valid)
    organizer_fm = _organizer_fm_class(starter_kit_dir)
    model = organizer_fm(dimension, k=config.k, lr=config.lr, seed=seed)
    rng = np.random.default_rng(seed)
    best_primary, best_state, bad_epochs = -1.0, None, 0
    started = perf_counter()
    for _epoch in range(1, config.epochs + 1):
        indices = rng.permutation(len(y_train))
        for start in range(0, len(indices), config.batch_size):
            batch = indices[start : start + config.batch_size]
            model.step(x_train[batch], y_train[batch])
        metrics = adapter.evaluator.score_development(
            "valid", users_valid, [int(row.label) for row in valid], model.predict(x_valid)
        )
        if metrics["primary"] > best_primary + 1e-5:
            best_primary, bad_epochs = metrics["primary"], 0
            best_state = (model.V.copy(), model.W.copy(), np.float32(model.b))
        else:
            bad_epochs += 1
            if bad_epochs >= config.patience:
                break
    if best_state is None:
        raise RuntimeError("baseline did not produce a checkpoint")
    model.V, model.W, model.b = best_state
    metrics = adapter.evaluator.score_development(
        "valid", users_valid, [int(row.label) for row in valid], model.predict(x_valid)
    )
    metrics["wall_seconds"] = perf_counter() - started
    metrics["seed"] = float(seed)
    return metrics

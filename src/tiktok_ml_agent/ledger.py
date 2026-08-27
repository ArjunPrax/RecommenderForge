"""Append-only SQLite evidence ledger."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .contracts import RunRecord, RunStatus, utc_now


TERMINAL_STATUSES = {
    RunStatus.SUCCEEDED.value,
    RunStatus.FAILED.value,
    RunStatus.RECOVERED.value,
    RunStatus.REJECTED.value,
}


class ExperimentLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def close(self) -> None:
        self.connection.close()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                run_class TEXT NOT NULL,
                status TEXT NOT NULL,
                benchmark_id TEXT NOT NULL,
                operator_family TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(run_id)
            );
            CREATE TABLE IF NOT EXISTS memory_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                source_run_count INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def create_run(self, record: RunRecord) -> None:
        payload = json.dumps(record.to_dict(), sort_keys=True)
        try:
            self.connection.execute(
                """
                INSERT INTO runs (
                    run_id, experiment_id, run_class, status, benchmark_id,
                    operator_family, payload_json, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    record.experiment_id,
                    str(record.run_class),
                    str(record.status),
                    record.benchmark_id,
                    str(record.operator_family),
                    payload,
                    record.created_at,
                    record.completed_at,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"run_id already exists: {record.run_id}") from exc
        self.connection.commit()

    def finalize_run(self, record: RunRecord) -> None:
        if str(record.status) not in TERMINAL_STATUSES:
            raise ValueError("only terminal run statuses can be finalized")
        existing = self.connection.execute(
            "SELECT status FROM runs WHERE run_id = ?", (record.run_id,)
        ).fetchone()
        if existing is None:
            raise KeyError(record.run_id)
        if existing["status"] in TERMINAL_STATUSES:
            raise ValueError(f"run {record.run_id} is immutable after finalization")
        record.completed_at = record.completed_at or utc_now()
        payload = json.dumps(record.to_dict(), sort_keys=True)
        self.connection.execute(
            """
            UPDATE runs
            SET status = ?, payload_json = ?, completed_at = ?
            WHERE run_id = ?
            """,
            (str(record.status), payload, record.completed_at, record.run_id),
        )
        self.connection.commit()

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        if not self.connection.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone():
            raise KeyError(run_id)
        self.connection.execute(
            "INSERT INTO events (run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (run_id, event_type, json.dumps(payload, sort_keys=True), utc_now()),
        )
        self.connection.commit()

    def get_run(self, run_id: str) -> dict[str, Any]:
        row = self.connection.execute("SELECT payload_json FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return json.loads(row["payload_json"])

    def list_runs(self) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT payload_json FROM runs ORDER BY created_at, run_id").fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def events_for(self, run_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT event_type, payload_json, created_at FROM events WHERE run_id = ? ORDER BY event_id",
            (run_id,),
        ).fetchall()
        return [
            {"event_type": row["event_type"], "payload": json.loads(row["payload_json"]), "created_at": row["created_at"]}
            for row in rows
        ]

    def save_memory_snapshot(self, snapshot_id: str, source_run_count: int, payload: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO memory_snapshots (snapshot_id, source_run_count, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (snapshot_id, source_run_count, json.dumps(payload, sort_keys=True), utc_now()),
        )
        self.connection.commit()

    def latest_memory_snapshot(self) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT snapshot_id, source_run_count, payload_json, created_at FROM memory_snapshots ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return {
            "snapshot_id": row["snapshot_id"],
            "source_run_count": row["source_run_count"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }

    def resource_totals(self, run_classes: Iterable[str] | None = None) -> dict[str, float]:
        allowed = set(run_classes or [])
        totals: dict[str, float] = {}
        for record in self.list_runs():
            if allowed and record["run_class"] not in allowed:
                continue
            for key, value in record.get("resource_usage", {}).items():
                totals[key] = totals.get(key, 0.0) + float(value)
        return totals

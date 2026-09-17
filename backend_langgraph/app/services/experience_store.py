"""本地数据飞轮与端到端链路穿刺存储。

SQLite 只保存结构化运行信号；完整请求和计划仅在用户开启学习授权时进入
episode 表。外部资料正文不写入事件，事件只记录 source/chunk 标识。
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(_redact(value), ensure_ascii=False, separators=(",", ":"))


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(secret in lowered for secret in ("api_key", "token", "password", "secret")):
                result[key] = "[REDACTED]"
            else:
                result[key] = _redact(item)
        return result
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


class ExperienceStore:
    def __init__(self, database_path: Optional[Path] = None):
        default_path = Path(__file__).resolve().parents[2] / "data" / "experience.db"
        self.database_path = Path(database_path or os.getenv("EXPERIENCE_DB_PATH", default_path))
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_trace ON events(trace_id, id);

                CREATE TABLE IF NOT EXISTS episodes (
                    trace_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    request_fingerprint TEXT NOT NULL,
                    request_json TEXT,
                    plan_json TEXT,
                    validation_score REAL,
                    solver_status TEXT,
                    repair_attempted INTEGER NOT NULL DEFAULT 0,
                    revision INTEGER NOT NULL DEFAULT 0,
                    latency_ms INTEGER NOT NULL DEFAULT 0,
                    learning_consent INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    accepted INTEGER NOT NULL,
                    rating INTEGER,
                    comment TEXT,
                    corrected_plan_json TEXT,
                    FOREIGN KEY(trace_id) REFERENCES episodes(trace_id)
                );
                """
            )

    def record_event(self, trace_id: str, stage: str, event_type: str, payload: Dict[str, Any]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO events(trace_id, created_at, stage, event_type, payload_json) VALUES (?, ?, ?, ?, ?)",
                (trace_id, _utc_now(), stage, event_type, _json(payload)),
            )

    def save_episode(self, trace_id: str, request: Any, plan: Any, latency_ms: int) -> None:
        request_data = request.model_dump(mode="json") if hasattr(request, "model_dump") else request
        plan_data = plan.model_dump(mode="json") if hasattr(plan, "model_dump") else plan
        consent = bool(request_data.get("enable_experience_learning", False))
        fingerprint_payload = {key: value for key, value in request_data.items() if key != "free_text_input"}
        fingerprint = hashlib.sha256(_json(fingerprint_payload).encode("utf-8")).hexdigest()[:20]
        validation = plan_data.get("validation_report") or {}
        optimization = plan_data.get("optimization_report") or {}
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO episodes(
                    trace_id, created_at, request_fingerprint, request_json, plan_json,
                    validation_score, solver_status, repair_attempted, revision, latency_ms,
                    learning_consent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    _utc_now(),
                    fingerprint,
                    _json(request_data) if consent else None,
                    _json(plan_data) if consent else None,
                    validation.get("score"),
                    optimization.get("status"),
                    int(bool(validation.get("repair_attempted"))),
                    int(plan_data.get("revision", 0)),
                    latency_ms,
                    int(consent),
                ),
            )

    def add_feedback(
        self,
        trace_id: str,
        accepted: bool,
        rating: Optional[int],
        comment: str,
        corrected_plan: Any = None,
    ) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO feedback(trace_id, created_at, accepted, rating, comment, corrected_plan_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    _utc_now(),
                    int(accepted),
                    rating,
                    comment[:2000],
                    _json(corrected_plan) if corrected_plan is not None else None,
                ),
            )
            return int(cursor.lastrowid)

    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        with self._connect() as connection:
            episode = connection.execute("SELECT * FROM episodes WHERE trace_id = ?", (trace_id,)).fetchone()
            events = connection.execute(
                "SELECT created_at, stage, event_type, payload_json FROM events WHERE trace_id = ? ORDER BY id",
                (trace_id,),
            ).fetchall()
            feedback = connection.execute(
                "SELECT created_at, accepted, rating, comment FROM feedback WHERE trace_id = ? ORDER BY id",
                (trace_id,),
            ).fetchall()
        return {
            "trace_id": trace_id,
            "episode": dict(episode) if episode else None,
            "events": [
                {**dict(row), "payload": json.loads(row["payload_json"])} for row in events
            ],
            "feedback": [dict(row) for row in feedback],
        }

    def hard_cases(self, limit: int = 100) -> List[Dict[str, Any]]:
        query = """
            SELECT e.*,
                   COUNT(f.id) AS feedback_count,
                   MIN(CASE WHEN f.accepted = 0 THEN 0 ELSE 1 END) AS all_feedback_accepted
            FROM episodes e
            LEFT JOIN feedback f ON f.trace_id = e.trace_id
            WHERE e.learning_consent = 1
            GROUP BY e.trace_id
            HAVING e.validation_score < 1.0
                OR e.repair_attempted = 1
                OR e.revision > 0
                OR e.solver_status NOT IN ('OPTIMAL', 'FEASIBLE')
                OR all_feedback_accepted = 0
            ORDER BY e.created_at DESC
            LIMIT ?
        """
        with self._connect() as connection:
            rows = connection.execute(query, (limit,)).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> Dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS episodes,
                       SUM(learning_consent) AS consented_episodes,
                       AVG(validation_score) AS average_validation_score,
                       AVG(latency_ms) AS average_latency_ms,
                       SUM(CASE WHEN repair_attempted = 1 THEN 1 ELSE 0 END) AS repaired_episodes,
                       SUM(CASE WHEN revision > 0 THEN 1 ELSE 0 END) AS replanned_episodes
                FROM episodes
                """
            ).fetchone()
            feedback = connection.execute(
                "SELECT COUNT(*) AS total, AVG(rating) AS average_rating, AVG(accepted) AS acceptance_rate FROM feedback"
            ).fetchone()
        return {"episodes": dict(row), "feedback": dict(feedback), "database_path": str(self.database_path)}


_store: Optional[ExperienceStore] = None


def get_experience_store() -> ExperienceStore:
    global _store
    if _store is None:
        _store = ExperienceStore()
    return _store

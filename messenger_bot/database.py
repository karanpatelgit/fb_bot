import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterable


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    psid TEXT PRIMARY KEY,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    name TEXT,
                    birthday TEXT,
                    preferred_language TEXT DEFAULT 'hinglish',
                    subscribed INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE,
                    psid TEXT NOT NULL,
                    sender_type TEXT NOT NULL,
                    text TEXT,
                    topic TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memory (
                    psid TEXT PRIMARY KEY,
                    preferences TEXT DEFAULT '{}',
                    notes TEXT DEFAULT '',
                    updated_at TEXT NOT NULL
                );
                """
            )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def ensure_user(self, psid: str) -> bool:
        now = self._now()
        with self._conn() as conn:
            row = conn.execute("SELECT psid FROM users WHERE psid = ?", (psid,)).fetchone()
            if row:
                conn.execute("UPDATE users SET last_seen = ? WHERE psid = ?", (now, psid))
                return False
            conn.execute(
                "INSERT INTO users (psid, first_seen, last_seen) VALUES (?, ?, ?)",
                (psid, now, now),
            )
            conn.execute(
                "INSERT INTO memory (psid, updated_at) VALUES (?, ?)",
                (psid, now),
            )
            return True

    def is_duplicate_message(self, message_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute("SELECT message_id FROM messages WHERE message_id = ?", (message_id,)).fetchone()
            return row is not None

    def add_message(self, message_id: str | None, psid: str, sender_type: str, text: str, topic: str = "general"):
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO messages (message_id, psid, sender_type, text, topic, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (message_id, psid, sender_type, text, topic, self._now()),
            )

    def get_last_messages(self, psid: str, limit: int = 10) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT sender_type, text, created_at
                FROM messages
                WHERE psid = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (psid, limit),
            ).fetchall()
            return [dict(r) for r in reversed(rows)]

    def update_name(self, psid: str, name: str):
        with self._conn() as conn:
            conn.execute("UPDATE users SET name = ? WHERE psid = ?", (name, psid))

    def update_birthday(self, psid: str, birthday: str):
        with self._conn() as conn:
            conn.execute("UPDATE users SET birthday = ? WHERE psid = ?", (birthday, psid))

    def update_language(self, psid: str, language: str):
        with self._conn() as conn:
            conn.execute("UPDATE users SET preferred_language = ? WHERE psid = ?", (language, psid))

    def get_user_profile(self, psid: str) -> dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE psid = ?", (psid,)).fetchone()
            if not row:
                return {}
            return dict(row)

    def set_memory(self, psid: str, preferences: dict[str, Any], notes: str):
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO memory (psid, preferences, notes, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(psid) DO UPDATE SET
                    preferences=excluded.preferences,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at
                """,
                (psid, json.dumps(preferences, ensure_ascii=False), notes, self._now()),
            )

    def get_memory(self, psid: str) -> dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute("SELECT preferences, notes FROM memory WHERE psid = ?", (psid,)).fetchone()
            if not row:
                return {"preferences": {}, "notes": ""}
            return {"preferences": json.loads(row["preferences"] or "{}"), "notes": row["notes"] or ""}

    def get_subscribers(self) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT psid FROM users WHERE subscribed = 1").fetchall()
            return [r["psid"] for r in rows]

    def set_subscribed(self, psid: str, subscribed: bool):
        with self._conn() as conn:
            conn.execute("UPDATE users SET subscribed = ? WHERE psid = ?", (1 if subscribed else 0, psid))

    def get_stats(self) -> dict[str, Any]:
        today = datetime.now(timezone.utc).date().isoformat()
        with self._conn() as conn:
            total_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
            messages_today = conn.execute(
                "SELECT COUNT(*) AS c FROM messages WHERE substr(created_at, 1, 10) = ?",
                (today,),
            ).fetchone()["c"]
            popular = conn.execute(
                """
                SELECT topic, COUNT(*) AS count
                FROM messages
                WHERE sender_type = 'user'
                GROUP BY topic
                ORDER BY count DESC
                LIMIT 5
                """
            ).fetchall()
        return {
            "total_users": total_users,
            "messages_today": messages_today,
            "popular_topics": [dict(r) for r in popular],
        }

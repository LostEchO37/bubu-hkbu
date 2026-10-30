"""SQLite storage for accounts and synced student data."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "users.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                display_name TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_data (
                user_id INTEGER PRIMARY KEY,
                profile_json TEXT NOT NULL,
                messages_json TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )


def upsert_user_data(user_id: int, profile_json: str, messages_json: str) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO user_data (user_id, profile_json, messages_json, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                profile_json = excluded.profile_json,
                messages_json = excluded.messages_json,
                updated_at = datetime('now')
            """,
            (user_id, profile_json, messages_json),
        )
        conn.commit()


def fetch_user_data(user_id: int) -> tuple[str, str] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT profile_json, messages_json FROM user_data WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return row["profile_json"], row["messages_json"]

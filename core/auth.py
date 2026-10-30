"""Simple local login (demo / course project — not production SSO)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from core.database import _connect, fetch_user_data, init_db, upsert_user_data


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return digest.hex()


def register_user(username: str, password: str, display_name: str = "") -> tuple[bool, str]:
    init_db()
    username = username.strip().lower()
    if len(username) < 3:
        return False, "username_too_short"
    if len(password) < 6:
        return False, "password_too_short"
    salt = secrets.token_hex(16)
    pwd_hash = _hash_password(password, salt)
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, salt, display_name) VALUES (?, ?, ?, ?)",
                (username, pwd_hash, salt, display_name.strip()),
            )
            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO user_data (user_id, profile_json, messages_json) VALUES (?, ?, ?)",
                (user_id, "{}", "[]"),
            )
            conn.commit()
        return True, "ok"
    except Exception:
        return False, "username_taken"


def login_user(username: str, password: str) -> tuple[int | None, str]:
    init_db()
    username = username.strip().lower()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, password_hash, salt, display_name FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if not row:
        return None, "invalid"
    expected = row["password_hash"]
    actual = _hash_password(password, row["salt"])
    if not hmac.compare_digest(expected, actual):
        return None, "invalid"
    return int(row["id"]), row["display_name"] or username


def get_user_by_id(user_id: int) -> tuple[str, str] | None:
    """Return (username, display_name) for a valid user id, else None."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT username, display_name FROM users WHERE id = ?",
            (int(user_id),),
        ).fetchone()
    if not row:
        return None
    username = str(row["username"] or "")
    display = str(row["display_name"] or "") or username
    return username, display


def save_session(user_id: int, profile_json: str, messages_json: str) -> None:
    init_db()
    upsert_user_data(user_id, profile_json, messages_json)


def load_session(user_id: int) -> tuple[dict, list] | None:
    init_db()
    raw = fetch_user_data(user_id)
    if not raw:
        return {}, []
    import json

    profile_json, messages_json = raw
    profile = json.loads(profile_json) if profile_json else {}
    messages = json.loads(messages_json) if messages_json else []
    return profile, messages

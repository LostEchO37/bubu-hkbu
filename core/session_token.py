"""Signed auth tokens so HTML bubble links can survive full page reloads.

Streamlit session_state dies when the browser navigates via <a href="?…">.
A short-lived HMAC token in the query string restores the logged-in user.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from pathlib import Path

_SECRET_FILE = Path(__file__).resolve().parents[1] / "data" / ".session_secret"
_MAX_AGE_SEC = 60 * 60 * 24 * 7  # 7 days


def _secret() -> bytes:
    env = os.environ.get("HKBU_SESSION_SECRET", "").strip()
    if env:
        return env.encode("utf-8")
    _SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    if _SECRET_FILE.exists():
        return _SECRET_FILE.read_bytes()
    secret = os.urandom(32)
    _SECRET_FILE.write_bytes(secret)
    try:
        _SECRET_FILE.chmod(0o600)
    except OSError:
        pass
    return secret


def make_auth_token(user_id: int) -> str:
    ts = int(time.time())
    payload = f"{int(user_id)}.{ts}"
    sig = hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"{payload}.{sig}"


def verify_auth_token(token: str | None) -> int | None:
    if not token or token.count(".") != 2:
        return None
    uid_s, ts_s, sig = token.split(".", 2)
    try:
        uid = int(uid_s)
        ts = int(ts_s)
    except ValueError:
        return None
    if abs(int(time.time()) - ts) > _MAX_AGE_SEC:
        return None
    payload = f"{uid}.{ts}"
    expect = hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(expect, sig):
        return None
    return uid

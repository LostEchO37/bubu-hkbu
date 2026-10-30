#!/usr/bin/env python3
"""End-to-end: auth survives wake/pick HTML navigation intents."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

from core.auth import get_user_by_id, login_user, register_user  # noqa: E402
from core.database import init_db  # noqa: E402
from core.session_token import make_auth_token, verify_auth_token  # noqa: E402


def _seed_user() -> tuple[int, str]:
    init_db()
    register_user("__bubble_test__", "bubbletest99", "Test")
    uid, _ = login_user("__bubble_test__", "bubbletest99")
    assert uid, "seed login failed"
    token = make_auth_token(int(uid))
    assert verify_auth_token(token) == int(uid)
    assert get_user_by_id(int(uid))
    return int(uid), token


def main() -> None:
    uid, token = _seed_user()
    app = str(ROOT / "app.py")

    # 1) Wake with auth → stay logged in + burst
    at = AppTest.from_file(app, default_timeout=90)
    at.query_params["auth"] = token
    at.query_params["wake"] = "1"
    at.run(timeout=90)
    assert not at.exception, at.exception
    assert at.session_state.get("user_id") == uid, "wake must restore login"
    assert at.session_state.get("agent_burst") is True, "wake must open burst"
    html = "\n".join(getattr(el, "value", "") or "" for el in at.html)
    assert "bu-prompt" in html or "bu-cell" in html, "prompt cards must render"
    assert "auth=" in html, "prompt links must carry auth"

    # 2) Pick with auth from fresh session → stay logged in (not kicked to login)
    at2 = AppTest.from_file(app, default_timeout=90)
    at2.query_params["auth"] = token
    at2.query_params["pick"] = "0"
    at2.run(timeout=90)
    assert not at2.exception, at2.exception
    assert at2.session_state.get("user_id") == uid, "pick must restore login"
    assert at2.session_state.get("agent_burst") is True, "pick should leave hub"

    # 3) Auth missing → login screen (no crash)
    at3 = AppTest.from_file(app, default_timeout=90)
    at3.query_params["wake"] = "1"
    at3.run(timeout=90)
    assert not at3.exception, at3.exception
    assert not at3.session_state.get("user_id"), "no auth → not logged in"

    print("check_bubble_flow: ok")


if __name__ == "__main__":
    main()

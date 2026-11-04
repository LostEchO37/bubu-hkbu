#!/usr/bin/env python3
"""Self-check: hub/burst HTML contains true circular bubbles (no st.button)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = "http://127.0.0.1:8501"
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> None:
    # AppTest does not need a live server; HTTP probe is optional.
    try:
        _get(ROOT)
    except (urllib.error.URLError, TimeoutError, OSError):
        pass

    from streamlit.testing.v1 import AppTest

    from core.app_settings import AppSettings
    from core.auth import login_user, register_user
    from core.database import init_db
    from core.i18n import t
    from core.profile import StudentProfile

    # Keep in sync with app._UI_REVISION — mismatch forces DB reload → reset_to_hub.
    ui_revision = 21
    for line in (ROOT_DIR / "app.py").read_text(encoding="utf-8").splitlines():
        if line.startswith("_UI_REVISION"):
            ui_revision = int(line.split("=", 1)[1].strip())
            break

    init_db()
    ok, _ = register_user("__bubble_test__", "bubbletest99", "Test")
    uid, err = login_user("__bubble_test__", "bubbletest99")
    if not uid:
        print(f"check_bubble_visual: login failed: {err}", file=sys.stderr)
        sys.exit(1)

    lang = "zh-CN"
    welcome = t("welcome", lang)

    def _seed(at: AppTest, *, burst: bool) -> None:
        at.session_state["user_id"] = uid
        at.session_state["account_username"] = "__bubble_test__"
        at.session_state["display_name"] = "Test"
        at.session_state["profile"] = StudentProfile()
        at.session_state["messages"] = [{"role": "assistant", "content": welcome}]
        at.session_state["agent_burst"] = burst
        at.session_state["_db_loaded"] = True
        at.session_state["_ui_revision"] = ui_revision
        at.session_state["app_settings"] = AppSettings()

    def _html_blob(at: AppTest) -> str:
        return "\n".join(getattr(el, "value", "") or "" for el in at.html)

    # --- Hub phase ---
    at = AppTest.from_file(str(ROOT_DIR / "app.py"), default_timeout=90)
    _seed(at, burst=False)
    at.run(timeout=90)
    assert not at.exception, f"hub error: {at.exception}"

    html_blob = _html_blob(at)
    assert "bu-cta" in html_blob, "hub HTML missing CTA"
    assert not any(b.key == "hub_blob_tap" for b in at.button), "hub must not use st.button"
    assert "wake" in html_blob

    # --- Burst phase ---
    at2 = AppTest.from_file(str(ROOT_DIR / "app.py"), default_timeout=90)
    _seed(at2, burst=True)
    at2.run(timeout=90)
    assert not at2.exception, f"burst error: {at2.exception}"

    burst_html = _html_blob(at2)
    assert "bu-prompt" in burst_html, "burst missing prompt cards"
    assert "bu-card-in" in burst_html, "stagger animation missing"
    assert "pick=0" in burst_html and "pick=4" in burst_html
    assert not any(getattr(b, "key", "") and str(b.key).startswith("daughter_") for b in at2.button)

    print(json.dumps({"ok": True, "hub": "bu-cta", "burst": "bu-prompt x5", "register_ok": ok, "ui_revision": ui_revision}))


if __name__ == "__main__":
    main()

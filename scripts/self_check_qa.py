#!/usr/bin/env python3
"""Full self-check: imports, smoke, clock, i18n keys."""

from __future__ import annotations

import importlib
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    mods = [
        "app",
        "core.home_agent",
        "core.ui",
        "core.i18n",
        "core.agent",
        "core.today",
        "core.profile",
        "core.timetable_vision",
        "core.mail_vision",
        "core.identity",
    ]
    for m in mods:
        importlib.import_module(m)

    from app import _UI_REVISION
    from core.i18n import MESSAGES, t
    from core.mail_vision import MailDraftResult, _parse_payload, format_draft_for_chat
    from core.profile import CourseSlot, StudentProfile
    from core.timetable_vision import _snap_hkbu_times
    from core.today import clock_status, detect_reminders, pulse_html, remaining_free_gaps

    assert _UI_REVISION >= 20

    from core.changelog import changelog_markdown

    md = changelog_markdown("zh-CN")
    assert "v0.1" in md and "v0.26" in md
    assert (ROOT / "assets" / "bu_favicon.png").is_file()
    assert t("chunk_reload_tip", "zh-CN")
    assert t("workspace_toggle", "en")
    ext_bg = (ROOT / "extension" / "background.js").read_text(encoding="utf-8")
    ext_ct = (ROOT / "extension" / "content.js").read_text(encoding="utf-8")
    assert "bubu-hkbu.streamlit.app" in ext_bg
    assert 'DEFAULT_APP_URL = "https://bubu-hkbu.streamlit.app"' in ext_bg
    assert "bubu_lang" in ext_bg and "bubu-set-lang" in ext_bg
    assert "isStreamlitHost" in ext_bg
    assert "if (tabUrl && isStreamlitHost(tabUrl)) return;" in ext_bg
    assert "zh-TW" in ext_ct and "lang-sat" in ext_ct
    assert "lang-chip" not in ext_ct
    assert "streamlit.app" in ext_ct
    assert "inject_chunk_recovery" in (ROOT / "app.py").read_text(encoding="utf-8")
    assert "workspace_panel_open" in (ROOT / "app.py").read_text(encoding="utf-8")
    ui_src = (ROOT / "core" / "ui.py").read_text(encoding="utf-8")
    assert "_bubu_chunk_guard_injected" in ui_src
    assert "components.html" not in ui_src
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "streamlit>=" in req
    assert "safe_st_html" in ui_src
    from core.ui import inject_chunk_recovery, safe_st_html

    assert callable(inject_chunk_recovery) and callable(safe_st_html)
    assert "密钥" not in md and "secret" not in md.lower()
    assert "OPENAI" not in md and "LostEchO" not in md
    assert t("changelog_privacy", "en")

    for key in (
        "tt_ready_hint",
        "hub_credit",
        "changelog_title",
        "pulse_today",
        "remind_rush",
        "countdown_exam_sem1",
        "scan_email_reply",
        "email_section",
        "upload_email_shot",
        "email_tone",
        "email_tone_polite",
        "email_add_tasks",
        "plugin_section",
        "plugin_download",
    ):
        assert key in MESSAGES
        text = t(key, "zh-CN")
        assert text and text != key, key

    from core.extension_pack import extension_zip_bytes

    z = extension_zip_bytes()
    assert z[:2] == b"PK" and len(z) > 500
    assert (ROOT / "extension" / "manifest.json").is_file()
    assert "bubu-fab" in (ROOT / "extension" / "content.js").read_text(encoding="utf-8")

    sample = _parse_payload(
        '{"subject":"HW","from":"t@hkbu.edu.hk","date":"","summary":"Submit HW",'
        '"key_points":["due Fri"],"tasks":[{"title":"HW","due":"2026-11-01"}],'
        '"reply_subject":"Re: HW","reply_body":"Dear teacher,\\nI will submit by Friday.\\n\\n[Your name]"}'
    )
    assert isinstance(sample, MailDraftResult)
    assert "Friday" in sample.reply_body
    assert "建议回复" in format_draft_for_chat(sample, "zh-CN")

    assert _snap_hkbu_times("09:30", "11:30") == ("09:30", "11:20")

    p = StudentProfile(
        timetable=[
            CourseSlot("UCLC1009", "", "Fri", "11:30", "13:20", "OEE1017"),
            CourseSlot("BUSI1006", "", "Fri", "15:30", "17:20", "WLB204"),
            CourseSlot("A", "", "Mon", "09:30", "11:20", "OEE1017"),
            CourseSlot("B", "", "Mon", "11:30", "12:20", "FSC801C"),
        ]
    )
    now = datetime(2026, 10, 30, 13, 2)
    st = clock_status(p, now=now)
    assert st.state == "in_class" and st.free_from_hhmm == "13:20"
    gaps = remaining_free_gaps(p, now=now, min_minutes=30)
    assert gaps and gaps[0][0] == "13:20"
    assert any(r.kind == "rush" for r in detect_reminders(p))
    assert "bu-pulse" in pulse_html(p, "zh-CN", now=now)

    from scripts.smoke_ui_flow import main as smoke
    from scripts.full_user_journey import main as journey

    smoke()
    journey()
    print("self_check_qa: ok")


if __name__ == "__main__":
    main()

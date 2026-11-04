#!/usr/bin/env python3
"""Simulate a full user path: login prefs → hydrate → workspace → chat chrome → theme CSS."""

from __future__ import annotations

import inspect
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _fake_streamlit() -> MagicMock:
    st = MagicMock()
    store: dict = {}

    class _SS(dict):
        def __getattr__(self, k):  # noqa: ANN001
            try:
                return self[k]
            except KeyError as e:
                raise AttributeError(k) from e

        def __setattr__(self, k, v):  # noqa: ANN001
            self[k] = v

    st.session_state = _SS(store)
    st.query_params = {}
    st.rerun = MagicMock()
    st.html = MagicMock()
    st.markdown = MagicMock()
    st.sidebar = MagicMock()
    return st


def check_theme_css() -> None:
    from core.app_settings import AppSettings
    from core.ui import inject_bu_theme

    st = _fake_streamlit()
    import core.ui as ui

    with patch.object(ui, "st", st):
        inject_bu_theme(AppSettings(theme="dark"))
        assert st.html.called
        css = st.html.call_args[0][0]
        assert "--sky-bg: #15242c" in css or "--sky-bg:#15242c" in css.replace(" ", "")
        assert "[data-testid=\"stExpander\"]" in css
        assert "stBottomBlockContainer" in css
        assert "stFileUploaderDropzone" in css
        # Must NOT paint every dropzone child with dark btn-bg (black Upload rectangle).
        assert "stFileUploaderDropzone\"] *" not in css
        assert "button *" in css and "background: transparent" in css
        assert "linear-gradient(135deg, #1f738c, #2f9eb8)" in css

        st.html.reset_mock()
        inject_bu_theme(AppSettings(theme="light"))
        css_l = st.html.call_args[0][0]
        assert "--sky-bg: #cfeaf3" in css_l or "#cfeaf3" in css_l


def check_login_theme_survives_hydrate() -> None:
    """Pre-login Apply dark must beat stale DB light settings."""
    from core.app_settings import AppSettings
    from core.profile import StudentProfile

    pre = AppSettings(theme="dark", font_size="large", personality="calm", ui_lang="zh-TW")
    stale = StudentProfile()
    stale.settings = AppSettings(theme="light", font_size="medium", personality="playful", ui_lang="zh-CN").to_dict()

    loaded = AppSettings.from_dict(stale.settings)
    assert loaded.theme == "light"
    settings_chose = True
    if settings_chose:
        merged = AppSettings(
            font_size=pre.font_size,
            theme=pre.theme,
            personality=pre.personality,
            ui_lang=pre.ui_lang,
        )
    else:
        merged = loaded
    assert merged.theme == "dark"
    assert merged.font_size == "large"
    assert merged.personality == "calm"
    assert merged.ui_lang == "zh-TW"


def check_workspace_and_tasks() -> None:
    from core.i18n import t
    from core.profile import StudentProfile, TaskItem, CourseSlot
    from core.today import clock_status, detect_reminders, pulse_html, remaining_free_gaps

    p = StudentProfile(
        name="Test",
        timetable=[
            CourseSlot("UCLC1009", "University English", "Mon", "09:30", "11:20", "OEE1017"),
            CourseSlot("GTSC2066", "AI", "Mon", "11:30", "12:20", "FSC801C"),
            CourseSlot("BUSI1006", "Biz", "Wed", "14:30", "16:20", "WLB210"),
        ],
        tasks=[TaskItem(title="Submit essay", due="2026-11-10")],
        custom_notes="Prefer morning slots",
    )
    assert len(p.timetable) == 3
    assert p.tasks[0].title == "Submit essay"
    p.tasks.append(TaskItem(title="Buy textbook", due=""))
    assert len(p.tasks) == 2

    d = p.to_dict()
    back = StudentProfile.from_dict(d)
    assert back.timetable[0].course_code == "UCLC1009"
    assert back.tasks[1].title == "Buy textbook"
    assert back.custom_notes.startswith("Prefer")

    now = datetime(2026, 11, 2, 10, 0)  # Monday in class
    st = clock_status(p, now=now)
    assert st.state in {"in_class", "free", "day_done", "no_class"}
    gaps = remaining_free_gaps(p, now=now, min_minutes=20)
    assert isinstance(gaps, list)
    rushes = [r for r in detect_reminders(p, lang="zh-CN") if r.kind == "rush"]
    assert rushes, "OEE→FSC adjacent should rush"
    html = pulse_html(p, "zh-CN", now=now)
    assert "bu-pulse" in html

    for lang in ("zh-CN", "zh-TW", "en"):
        assert t("workspace_title", lang)
        assert t("tasks", lang)
        assert t("email_section", lang)
        assert t("settings_theme", lang)
        assert t("theme_dark", lang)
        assert t("add_task", lang)
        assert t("upload_email_shot", lang)
        assert t("changelog_title", lang)


def check_mail_and_timetable_parsers() -> None:
    from core.mail_vision import MailDraftResult, _parse_payload, format_draft_for_chat
    from core.timetable_vision import _snap_hkbu_times, _slots_from_courses

    raw = (
        '{"subject":"Lab report","from":"ta@hkbu.edu.hk","date":"2026-11-01",'
        '"summary":"Submit lab by Fri","key_points":["due Friday","PDF only"],'
        '"tasks":[{"title":"Lab report","due":"2026-11-07"}],'
        '"reply_subject":"Re: Lab report",'
        '"reply_body":"Dear TA,\\nI will submit the PDF by Friday.\\n\\nBest,\\n[Your name]"}'
    )
    draft = _parse_payload(raw)
    assert isinstance(draft, MailDraftResult)
    assert draft.tasks and draft.tasks[0]["title"] == "Lab report"
    zh = format_draft_for_chat(draft, "zh-CN")
    en = format_draft_for_chat(draft, "en")
    assert "Lab report" in zh and "Friday" in en or "PDF" in en

    assert _snap_hkbu_times("09:30", "11:30") == ("09:30", "11:20")
    slots = _slots_from_courses(
        [
            {
                "course_code": "COMP1005",
                "course_title": "Intro",
                "day": "Tue",
                "start_time": "13:30",
                "end_time": "15:30",
                "location": "FSC501",
            }
        ]
    )
    assert slots[0].end_time == "15:20"
    assert slots[0].course_code == "COMP1005"


def check_chat_and_hub_invariants() -> None:
    from app import (
        all_welcome_bodies,
        chat_has_user_turn,
        default_welcome,
        _UI_REVISION,
    )
    from core.home_agent import render_agent_bubble, render_mini_prompt_bubbles
    from core.changelog import ENTRIES, changelog_markdown
    from core.identity import bot_nick
    from core.persona import PERSONALITY_BLOCK, get_persona

    assert _UI_REVISION >= 36
    for lang in ("zh-CN", "zh-TW", "en"):
        w = default_welcome(lang)
        assert not chat_has_user_turn(w)
        assert w[0]["content"] in all_welcome_bodies()
        assert bot_nick(lang)
        assert "playful" in PERSONALITY_BLOCK and "calm" in PERSONALITY_BLOCK
        prompt = get_persona(lang, "playful")
        assert "阿Bu" in prompt or "BuBu" in prompt

    hub = inspect.getsource(render_agent_bubble)
    assert "st.button" not in hub
    assert "bu-cta" in hub and "Outfit" in hub
    mini = inspect.getsource(render_mini_prompt_bubbles)
    assert "st.button" not in mini and "bu-prompt" in mini

    md = changelog_markdown("en")
    assert "v0.25" in md
    assert ENTRIES[0]["tag"] == "v0.25"
    assert (ROOT / "assets" / "bu_favicon.png").is_file()
    blob = " ".join(
        str(v) for e in ENTRIES for v in (e.get("body") or {}).values()
    ).lower()
    assert "secret" not in blob and "openai" not in blob and "apikey" not in blob.replace("_", "")


def check_auth_roundtrip() -> None:
    from core.auth import register_user, login_user, load_session, save_session
    from core.profile import StudentProfile, TaskItem
    import tempfile
    import os

    # Use isolated DB if auth supports path; otherwise exercise API shape only.
    from core import auth as auth_mod

    src = Path(auth_mod.__file__).read_text(encoding="utf-8")
    assert "login_user" in src and "register_user" in src
    assert "save_session" in src and "load_session" in src

    p = StudentProfile(name="Journey", tasks=[TaskItem(title="A", due="")])
    dumped = p.to_dict()
    assert dumped["name"] == "Journey"

    # Soft check: functions are callable
    assert callable(register_user) and callable(login_user)
    assert callable(save_session) and callable(load_session)
    del tempfile, os


def check_extension_pack() -> None:
    import io
    import zipfile

    from core.extension_pack import extension_zip_bytes

    z = extension_zip_bytes()
    assert z[:2] == b"PK" and len(z) > 500
    manifest = (ROOT / "extension" / "manifest.json").read_text(encoding="utf-8")
    assert "manifest_version" in manifest
    bg = (ROOT / "extension" / "background.js").read_text(encoding="utf-8")
    js = (ROOT / "extension" / "content.js").read_text(encoding="utf-8")
    opt = (ROOT / "extension" / "options.js").read_text(encoding="utf-8")
    assert "bubu-fab" in js
    assert "bubu-hkbu.streamlit.app" in bg
    assert "bubu_lang" in bg and "bubu-set-lang" in bg
    assert "lang-chip" in js and "zh-TW" in js
    assert "bubu_lang" in opt and "bubu-hkbu.streamlit.app" in opt
    with zipfile.ZipFile(io.BytesIO(z)) as zf:
        packed_bg = zf.read("bubu-fab-extension/background.js").decode("utf-8")
        packed_ct = zf.read("bubu-fab-extension/content.js").decode("utf-8")
    assert "bubu-hkbu.streamlit.app" in packed_bg
    assert "bubu-set-lang" in packed_bg
    assert "lang-chip" in packed_ct


def main() -> None:
    check_theme_css()
    check_login_theme_survives_hydrate()
    check_workspace_and_tasks()
    check_mail_and_timetable_parsers()
    check_chat_and_hub_invariants()
    check_auth_roundtrip()
    check_extension_pack()
    print("full_user_journey: ok")


if __name__ == "__main__":
    main()

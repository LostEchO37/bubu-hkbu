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
        "core.knowledge",
        "core.live_facts",
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
    assert "v0.1" in md and "v0.30" in md
    assert (ROOT / "assets" / "bu_favicon.png").is_file()
    assert t("chunk_reload_tip", "zh-CN")
    assert t("workspace_title", "en")
    ext_bg = (ROOT / "extension" / "background.js").read_text(encoding="utf-8")
    ext_ct = (ROOT / "extension" / "content.js").read_text(encoding="utf-8")
    assert 'DEFAULT_APP_URL = "https://bubu-hkbu.streamlit.app"' in ext_bg
    assert "bubu-hkbu-[a-z0-9]+" in ext_bg
    assert "waitTabComplete" in ext_bg
    assert "bubu_lang" in ext_bg and "bubu-set-lang" in ext_bg
    assert "isStreamlitHost" in ext_bg
    assert "if (tabUrl && isStreamlitHost(tabUrl)) return;" in ext_bg
    assert "zh-TW" in ext_ct and "lang-sat" in ext_ct
    assert "lang-chip" not in ext_ct
    assert "const R = 200" in ext_ct
    assert "const CW = 280" in ext_ct
    assert "backdrop-filter" not in ext_ct
    app_src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "_pending_pick" in app_src
    assert 'st.query_params["pick"] = str(pick)' not in app_src
    assert "inject_chunk_recovery" in app_src
    assert "nav_page" in app_src
    assert "render_app_sidebar" in app_src
    assert "render_tasks_page" in app_src
    assert "render_workspace_panel" in app_src
    assert "bu-login-shell" in app_src
    assert "dock_workspace_below_chat_input" not in app_src
    assert "data-bu-workspace-dock" not in app_src
    assert "main_chat(lang)" in app_src
    # Pages are exclusive — workspace/tasks not stacked under chat
    assert "workspace_panel_open" not in app_src
    assert 'page == "workspace"' in app_src and 'page == "tasks"' in app_src
    ui_src = (ROOT / "core" / "ui.py").read_text(encoding="utf-8")
    assert "_bubu_chunk_guard_injected" in ui_src
    assert "dock_workspace_below_chat_input" not in ui_src
    assert "Failed to fetch dynamically imported module" in ui_src
    assert "#F4F7F8" in ui_src and "#2F9EB8" in ui_src
    assert "max-width: 760px" in ui_src
    assert "fonts.googleapis.com" not in ui_src
    assert "feTurbulence" not in ui_src
    assert "components.html" not in ui_src
    assert "rgba(255,255,255,0.85)" not in ui_src
    assert "lru_cache" in (ROOT / "core" / "extension_pack.py").read_text(encoding="utf-8")
    ha_src = (ROOT / "core" / "home_agent.py").read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in ha_src
    assert t("cold_start_tip", "zh-CN")
    assert t("sharing_public_tip", "zh-CN")
    assert t("nav_chat", "en") and t("chat_empty_guide", "zh-CN")
    assert t("tasks_empty_cta", "en") and t("delete_task", "zh-TW")
    assert t("countdown_in_one_day", "en")
    assert "hub_wake_btn" in ha_src
    assert 'data-phase="hub"]) [data-testid="stBottomBlockContainer"]' not in ha_src
    assert 'st.chat_input(t("chat_placeholder", lang))' in app_src
    assert "chat_ready = not show_agent_hub" not in app_src
    assert "bubu_chunk_ts" in ui_src
    assert "chunk_reload_tip" in app_src  # still available in settings help
    # Deploy tips must not sit in the logged-in main stage path
    assert "st.caption(t(\"chunk_reload_tip\"" not in app_src.split("def main_chat")[1].split("def main")[0]
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

    from core.knowledge import retrieve, search_knowledge
    from core.live_facts import fetch_weather, official_links

    cal_hits = search_knowledge("第一学期考试周什么时候", top_k=4)
    assert cal_hits, "calendar RAG should return chunks"
    weather_bundle = retrieve("今天天气怎么样会下雨吗", top_k=4, lang="zh-CN")
    assert weather_bundle.live_facts and "天文台" in weather_bundle.live_facts
    assert weather_bundle.include_live_weather
    assert any("Observatory" in c for c in weather_bundle.citations)
    wx = fetch_weather("zh-CN")
    assert isinstance(wx.ok, bool)
    assert official_links("en") and "hko.gov.hk" in official_links("en")[0][1]
    assert t("rag_sources_title", "en") and t("link_hko", "zh-TW")
    assert (ROOT / "data" / "knowledge" / "official_links_zh.md").is_file()

    from scripts.smoke_ui_flow import main as smoke
    from scripts.full_user_journey import main as journey

    smoke()
    journey()
    print("self_check_qa: ok")


if __name__ == "__main__":
    main()

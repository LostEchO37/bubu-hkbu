#!/usr/bin/env python3
"""Self-check for chat hub / UI source invariants (run before asking user to test)."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import (  # noqa: E402
    _UI_REVISION,
    all_welcome_bodies,
    chat_has_user_turn,
    default_welcome,
)
from core import home_agent  # noqa: E402
from core.home_agent import _all_welcome_bodies, _short_label, render_agent_bubble  # noqa: E402


def main() -> None:
    lang = "zh-CN"
    welcome = default_welcome(lang)
    assert not chat_has_user_turn(welcome), "welcome-only should be pristine"
    assert welcome[0]["content"] in all_welcome_bodies()
    assert welcome[0]["content"] in _all_welcome_bodies()
    labels = [_short_label("x" * 80), "短"]
    assert labels[0].endswith("…")
    assert _UI_REVISION >= 20
    assert (ROOT / "extension" / "manifest.json").is_file()
    assert (ROOT / "extension" / "content.js").is_file()
    from core.extension_pack import extension_zip_bytes

    assert extension_zip_bytes()[:2] == b"PK"

    hub_src = inspect.getsource(render_agent_bubble)
    assert "st.button" not in hub_src, "hub must not use Streamlit buttons"
    assert "st.html" in hub_src
    assert "wake" in hub_src and "auth_token" in hub_src
    assert "bu-cta" in hub_src and "bu-title" in hub_src
    assert "bu-credit" in hub_src
    assert "GTSC2066 Group 16" in hub_src

    from core.identity import bot_nick
    from core.today import detect_reminders, format_countdown, next_countdown_event, pulse_html
    from core.profile import CourseSlot, StudentProfile

    assert bot_nick("zh-CN") == "阿Bu"
    assert bot_nick("en") == "BuBu"
    ev = next_countdown_event()
    assert ev is not None
    _, detail = format_countdown("zh-CN")
    assert detail
    demo = StudentProfile(
        timetable=[
            CourseSlot("A", "", "Mon", "09:30", "11:20", "OEE1017"),
            CourseSlot("B", "", "Mon", "11:30", "12:20", "FSC801C"),
        ]
    )
    rushes = [r for r in detect_reminders(demo, lang="zh-CN") if r.kind == "rush"]
    assert rushes, "OEE→FSC with standard 10 min break should rush-alert"
    assert "bu-pulse" in pulse_html(demo, "zh-CN")

    from core.timetable_vision import _snap_hkbu_times, _slots_from_courses

    assert _snap_hkbu_times("09:30", "11:30") == ("09:30", "11:20")
    assert _snap_hkbu_times("14:30", "16:20") == ("14:30", "16:20")
    fixed = _slots_from_courses(
        [{"course_code": "X", "day": "Wed", "start_time": "09:30", "end_time": "10:30", "location": "WLB"}]
    )
    assert fixed[0].end_time == "10:20"

    mini_src = inspect.getsource(home_agent.render_mini_prompt_bubbles)
    assert "st.button" not in mini_src
    assert "st.html" in mini_src
    assert "pick" in mini_src and "auth_token" in mini_src
    assert "bu-prompt" in mini_src
    assert "bu-card-in" in mini_src

    file_src = Path(home_agent.__file__).read_text(encoding="utf-8")
    assert "bu-cta" in file_src and "bu-prompt" in file_src

    from scripts.check_bubble_flow import main as flow_main

    flow_main()
    print("smoke_ui_flow: ok")


if __name__ == "__main__":
    main()

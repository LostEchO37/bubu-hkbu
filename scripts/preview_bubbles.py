"""Local visual preview of hub + burst bubbles (no auth)."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.home_agent import render_agent_bubble, render_mini_prompt_bubbles  # noqa: E402
from core.ui import inject_bu_theme, inject_ui_phase  # noqa: E402
from core.app_settings import AppSettings  # noqa: E402

st.set_page_config(page_title="Bubble Preview", layout="wide")
inject_bu_theme(AppSettings())

mode = st.sidebar.radio("phase", ["hub", "burst"], index=0)
if mode == "hub":
    inject_ui_phase("hub")
    render_agent_bubble("浸大同学助手 · 直接点击中央气泡", on_wake=lambda: None)
else:
    inject_ui_phase("burst")
    render_mini_prompt_bubbles(
        [
            "这学期校历里考试周是什么时候？",
            "CS 实验室 FSC801 开放时间？",
            "根据我的课表，帮我安排本周复习计划",
            "浸大 counselling 怎么预约？",
        ],
        plan_label="一键生成本周学习计划",
        hint="选一个气泡，开始聊天",
    )

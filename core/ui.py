"""Theme: campus morning light, soft teal water, light & dark, font scaling."""

from __future__ import annotations

import html

import streamlit as st

from core.app_settings import FONT_PX, HERO_SCALE, AppSettings


def inject_ui_phase(phase: str) -> None:
    """Mark UI phase for hub / burst / chat styling (import-safe entry point)."""
    from core.home_agent import _ensure_shell_css

    _ensure_shell_css(phase)  # type: ignore[arg-type]
    st.markdown(
        f'<div class="ui-phase-marker" data-phase="{phase}"></div>',
        unsafe_allow_html=True,
    )


def inject_bu_theme(settings: AppSettings) -> None:
    fs = FONT_PX.get(settings.font_size, "16px")
    hero = HERO_SCALE.get(settings.font_size, "1.65rem")

    if settings.theme == "dark":
        vars_css = """
  --sky: #3d8fab;
  --sky-deep: #5eb8d9;
  --sky-bg: #1a2a33;
  --cream: #243540;
  --cream-hover: #2c4150;
  --cream-border: #3d5565;
  --text: #e6f3f8;
  --text-soft: #a8c5d4;
  --app-bg: linear-gradient(165deg, #1c303a 0%, #15242c 42%, #101c22 100%);
  --sidebar-bg: linear-gradient(180deg, #162832 0%, #1e3440 100%);
  --accent-title: #7ec8e3;
  --grain: rgba(255,255,255,0.03);
"""
    else:
        vars_css = """
  --sky: #6ebfd8;
  --sky-deep: #2f9eb8;
  --sky-bg: #cfeaf3;
  --cream: #f7fbfd;
  --cream-hover: #eef7fa;
  --cream-border: #d2e6ee;
  --text: #1f4554;
  --text-soft: #4a6878;
  --app-bg: linear-gradient(168deg, #eef8fb 0%, #d8f0f7 36%, #bce4f0 70%, #a6d8e8 100%);
  --sidebar-bg: linear-gradient(180deg, #d8eef6 0%, #c2e3ef 100%);
  --accent-title: #1f738c;
  --grain: rgba(20, 55, 68, 0.025);
"""

    st.html(
        f"""
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
<style>
:root {{
{vars_css}
  --font-base: {fs};
  --font-hero: {hero};
}}

.stApp {{
  background: var(--app-bg) fixed;
  font-family: "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
    -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: var(--font-base);
  letter-spacing: 0.01em;
}}
.stApp::before {{
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse 62% 48% at 88% 6%, rgba(255,232,200,0.45), transparent 58%),
    radial-gradient(ellipse 55% 42% at 10% 90%, rgba(90,180,200,0.3), transparent 55%),
    radial-gradient(ellipse 42% 36% at 48% 42%, rgba(255,255,255,0.32), transparent 65%);
  animation: bu-sky 18s ease-in-out infinite alternate;
}}
.stApp::after {{
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.45;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.45'/%3E%3C/svg%3E");
  mix-blend-mode: soft-light;
}}
@keyframes bu-sky {{
  from {{ opacity: 0.86; transform: scale(1) translateY(0); }}
  to {{ opacity: 1; transform: scale(1.035) translateY(-1.2%); }}
}}

.block-container {{
  max-width: 920px;
  padding-top: 2.5rem;
  padding-bottom: 2rem;
  position: relative;
  z-index: 1;
}}

header[data-testid="stHeader"] {{
  background: transparent;
  pointer-events: none;
}}
header[data-testid="stHeader"] > div {{
  pointer-events: auto;
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] {{
  gap: 0.5rem;
  background: transparent;
}}

[data-testid="stSidebar"] {{
  background: var(--sidebar-bg);
  border-right: none !important;
  box-shadow: 6px 0 28px rgba(31, 115, 140, 0.08);
}}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
  line-height: 1.5;
  overflow-wrap: anywhere;
  word-break: break-word;
}}
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: normal !important;
}}
[data-testid="stSidebar"] {{
  overflow-x: hidden !important;
}}

.bu-hero {{
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,0.58);
  border-radius: 24px;
  padding: 1.5rem 1.65rem;
  margin-bottom: 1rem;
  box-shadow: 0 18px 44px rgba(31, 115, 140, 0.11);
  animation: bu-panel-in 0.5s cubic-bezier(.22,.9,.28,1) both;
}}
.bu-hero h1, .bu-hero h2 {{
  margin: 0.35rem 0 0;
  font-family: "Syne", "Noto Sans SC", sans-serif;
  font-size: var(--font-hero);
  font-weight: 750;
  color: var(--accent-title);
  line-height: 1.3;
  letter-spacing: -0.02em;
}}
.bu-hero p {{ margin: 0.55rem 0 0; color: var(--text-soft); line-height: 1.55; }}
.bu-hero.bu-login {{ margin-top: 0.25rem; }}
@keyframes bu-panel-in {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

section[data-testid="stSidebar"] .stButton > button {{
  border-radius: 999px !important;
  border: none !important;
  background: rgba(255, 255, 255, 0.58) !important;
  backdrop-filter: blur(8px) !important;
  color: var(--accent-title) !important;
  font-weight: 600 !important;
  font-size: var(--font-base) !important;
  box-shadow: 0 8px 20px rgba(31, 115, 140, 0.12) !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
  transform: translateY(-1px) !important;
  box-shadow: 0 12px 26px rgba(31, 115, 140, 0.16) !important;
}}
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stMain"] .stButton > button[kind="primary"] {{
  background: linear-gradient(135deg, #1f738c, #2f9eb8) !important;
  color: #f7fcff !important;
}}

[data-testid="stChatMessage"] {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}}

[data-testid="stChatInput"] > div {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}}
[data-testid="stChatInput"] textarea {{
  background: rgba(255, 255, 255, 0.62) !important;
  backdrop-filter: blur(18px) !important;
  color: var(--text) !important;
  font-size: var(--font-base) !important;
  border: 1px solid rgba(255,255,255,0.7) !important;
  border-radius: 999px !important;
  box-shadow: 0 14px 36px rgba(31, 115, 140, 0.13) !important;
  padding: 0.75rem 1.2rem !important;
  transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
}}
[data-testid="stChatInput"] textarea:focus {{
  border-color: rgba(47, 158, 184, 0.55) !important;
  box-shadow: 0 16px 40px rgba(31, 115, 140, 0.18) !important;
}}

h1, h2, h3, label, .stMarkdown, .stCaption, p {{ color: var(--text); }}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {{
  background: rgba(255, 255, 255, 0.78) !important;
  border: 1px solid rgba(255,255,255,0.85) !important;
  border-radius: 14px !important;
  color: var(--text) !important;
  box-shadow: 0 6px 18px rgba(31, 115, 140, 0.08) !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
  border-color: rgba(47, 158, 184, 0.55) !important;
  box-shadow: 0 8px 22px rgba(31, 115, 140, 0.14) !important;
}}
[data-baseweb="tab"] {{
  font-weight: 650 !important;
}}

#MainMenu, footer {{ visibility: hidden; }}

@media (prefers-reduced-motion: reduce) {{
  .stApp::before, .bu-hero {{ animation: none !important; }}
}}
</style>
        """,
        width="content",
    )


def render_login_header(title: str, hint: str) -> None:
    t, h = html.escape(title), html.escape(hint)
    st.html(
        f"""
<div class="bu-hero bu-login">
  <h2>{t}</h2>
  <p>{h}</p>
</div>
        """,
        width="stretch",
    )


def render_fun_home(greeting: str, tagline: str, tip: str, *, animate_in: bool = False) -> None:
    g, tg, tp = html.escape(greeting), html.escape(tagline), html.escape(tip)
    extra = " hero-chat-in" if animate_in else ""
    st.markdown(
        f"""
<div class="bu-hero{extra}">
  <p style="margin:0;font-size:1.05rem;color:var(--accent-title);font-weight:700;">{g}</p>
  <h1>{tg}</h1>
  <p>{tp}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


from core.home_agent import render_agent_bubble  # noqa: E402

__all__ = [
    "inject_bu_theme",
    "inject_ui_phase",
    "render_agent_bubble",
    "render_fun_home",
    "render_login_header",
]

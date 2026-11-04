"""Theme: campus morning light, soft teal water, light & dark, font scaling."""

from __future__ import annotations

import html
import inspect
from typing import Any

import streamlit as st

from core.app_settings import FONT_PX, HERO_SCALE, AppSettings


def safe_st_html(body: str, *, width: str = "content") -> None:
    """Call st.html across Streamlit versions (width / JS kwargs differ)."""
    kwargs: dict[str, Any] = {}
    try:
        params = inspect.signature(st.html).parameters
    except (TypeError, ValueError):
        params = {}
    if "width" in params:
        kwargs["width"] = width
    if "unsafe_allow_javascript" in params and "<script" in body.lower():
        kwargs["unsafe_allow_javascript"] = True
    try:
        st.html(body, **kwargs)
    except TypeError:
        # Extremely old / odd builds: positional only.
        st.html(body)


def inject_ui_phase(phase: str) -> None:
    """Mark UI phase for hub / burst / chat styling (import-safe entry point)."""
    from core.home_agent import _ensure_shell_css

    _ensure_shell_css(phase)  # type: ignore[arg-type]
    st.markdown(
        f'<div class="ui-phase-marker" data-phase="{phase}"></div>',
        unsafe_allow_html=True,
    )


def inject_chunk_recovery() -> None:
    """One-shot soft reload when Streamlit JS chunks fail after Cloud redeploy.

    Runs at most once per browser session flag in session_state so we do not
    mount a components iframe on every Streamlit rerun (that was a lag source).
    """
    if st.session_state.get("_bubu_chunk_guard_injected"):
        return
    st.session_state._bubu_chunk_guard_injected = True
    # Prefer st.html + JS flag when available; avoid components iframe spam.
    script = """
<script>
(function () {
  if (window.__bubuChunkGuard) return;
  window.__bubuChunkGuard = true;
  function isChunkFail(err) {
    var s = String((err && err.message) || err || "");
    return (
      s.indexOf("Failed to fetch dynamically imported module") >= 0 ||
      s.indexOf("Importing a module script failed") >= 0 ||
      s.indexOf("error loading dynamically imported module") >= 0
    );
  }
  function recover() {
    try {
      if (sessionStorage.getItem("bubu_chunk_reload") === "1") return;
      sessionStorage.setItem("bubu_chunk_reload", "1");
      var u = new URL(location.href);
      u.searchParams.set("_bubu_r", String(Date.now()));
      location.replace(u.toString());
    } catch (e) {
      location.reload();
    }
  }
  window.addEventListener("unhandledrejection", function (ev) {
    if (isChunkFail(ev.reason)) recover();
  });
  window.addEventListener("error", function (ev) {
    if (isChunkFail(ev && ev.error)) recover();
  }, true);
  setTimeout(function () {
    try { sessionStorage.removeItem("bubu_chunk_reload"); } catch (e) {}
  }, 20000);
})();
</script>
"""
    try:
        safe_st_html(script, width="content")
    except Exception:
        pass


def inject_bu_theme(settings: AppSettings) -> None:
    fs = FONT_PX.get(settings.font_size, "16px")
    hero = HERO_SCALE.get(settings.font_size, "1.65rem")
    # Corrupt / missing theme must never silently become dark.
    is_dark = settings.theme == "dark"

    if is_dark:
        vars_css = """
  --sky: #3d8fab;
  --sky-deep: #5eb8d9;
  --sky-bg: #15242c;
  --cream: #243540;
  --cream-hover: #2c4150;
  --cream-border: #3d5565;
  --text: #e6f3f8;
  --text-soft: #a8c5d4;
  --field-bg: #1b2c36;
  --field-text: #e6f3f8;
  --field-border: #3d5565;
  --app-bg: linear-gradient(165deg, #1c303a 0%, #15242c 42%, #101c22 100%);
  --sidebar-bg: linear-gradient(180deg, #162832 0%, #1e3440 100%);
  --accent-title: #7ec8e3;
  --hero-bg: rgba(36, 53, 64, 0.72);
  --hero-border: rgba(126, 200, 227, 0.22);
  --grain: rgba(255,255,255,0.03);
  --glow-a: rgba(94, 184, 217, 0.16);
  --glow-b: rgba(47, 158, 184, 0.12);
  --glow-c: rgba(30, 60, 72, 0.35);
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
  --field-bg: rgba(255, 255, 255, 0.86);
  --field-text: #1f4554;
  --field-border: rgba(255,255,255,0.85);
  --app-bg: linear-gradient(168deg, #eef8fb 0%, #d8f0f7 36%, #bce4f0 70%, #a6d8e8 100%);
  --sidebar-bg: linear-gradient(180deg, #d8eef6 0%, #c2e3ef 100%);
  --accent-title: #1f738c;
  --hero-bg: rgba(255, 255, 255, 0.5);
  --hero-border: rgba(255,255,255,0.58);
  --grain: rgba(20, 55, 68, 0.025);
  --glow-a: rgba(255,232,200,0.45);
  --glow-b: rgba(90,180,200,0.3);
  --glow-c: rgba(255,255,255,0.32);
"""

    btn_bg = "#1b2c36" if is_dark else "rgba(255,255,255,0.86)"
    btn_fg = "#e8f6fb" if is_dark else "#1f4554"
    exp_bg = "#243540" if is_dark else "#f7fbfd"
    exp_fg = "#e8f6fb" if is_dark else "#1f4554"
    # st.html with style-only goes to the event container (not shown as page text).
    # Never put raw HTML tags inside CSS comments — sanitizers break the style block.
    safe_st_html(
        f"""
<style>
@import url("https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap");
:root {{
{vars_css}
  --font-base: {fs};
  --font-hero: {hero};
  --btn-bg: {btn_bg};
  --btn-fg: {btn_fg};
  --exp-bg: {exp_bg};
  --exp-fg: {exp_fg};
}}

.stApp {{
  background: var(--app-bg) fixed;
  background-color: var(--sky-bg) !important;
  color: var(--text);
  font-family: "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
    -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: var(--font-base);
  letter-spacing: 0.01em;
}}
.stApp [data-testid="stAppViewContainer"],
.stApp [data-testid="stAppViewContainer"] > .main,
.stApp section.main,
.stApp .main .block-container {{
  background: transparent !important;
  background-color: transparent !important;
}}
.stApp::before {{
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse 62% 48% at 88% 6%, var(--glow-a), transparent 58%),
    radial-gradient(ellipse 55% 42% at 10% 90%, var(--glow-b), transparent 55%),
    radial-gradient(ellipse 42% 36% at 48% 42%, var(--glow-c), transparent 65%);
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
  max-width: 1180px;
  padding-top: 1.75rem;
  padding-bottom: 2rem;
  position: relative;
  z-index: 1;
  background: transparent !important;
}}

.bu-workspace-head {{
  margin: 0 0 0.85rem;
  padding: 0.85rem 1rem;
  border-radius: 18px;
  background: var(--hero-bg, rgba(255,255,255,0.55));
  border: 1px solid var(--hero-border, rgba(255,255,255,0.6));
  box-shadow: 0 10px 28px rgba(31, 115, 140, 0.08);
}}
.bu-workspace-head h3 {{
  margin: 0;
  font-family: "Outfit", "Noto Sans SC", sans-serif;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--accent-title);
  letter-spacing: -0.01em;
}}
.bu-workspace-head p {{
  margin: 0.35rem 0 0;
  color: var(--text-soft);
  font-size: 0.86rem;
  line-height: 1.45;
}}

header[data-testid="stHeader"] {{
  background: transparent;
  pointer-events: none;
}}
header[data-testid="stHeader"] > div {{
  pointer-events: auto;
}}
.bu-changelog-bar {{
  margin: 0 0 0.55rem;
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] {{
  gap: 0.5rem;
  background: transparent;
}}

[data-testid="stSidebar"] {{
  background: var(--sidebar-bg);
  border-right: none !important;
  box-shadow: 6px 0 28px rgba(31, 115, 140, 0.08);
  overflow-x: hidden !important;
  color: var(--text);
}}
/* Do NOT force color on every descendant — that made select text invisible in dark mode. */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {{
  color: var(--text) !important;
}}
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

/* Selects / radios readable in both themes */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="base-input"],
[data-testid="stSidebar"] div[data-baseweb="select"] {{
  background-color: var(--field-bg) !important;
  color: var(--field-text) !important;
  border-color: var(--field-border) !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-baseweb="select"] input {{
  color: var(--field-text) !important;
  -webkit-text-fill-color: var(--field-text) !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label,
[data-testid="stSidebar"] [role="radiogroup"] p,
[data-testid="stSidebar"] [role="radiogroup"] span {{
  color: var(--text) !important;
}}

.bu-hero {{
  background: var(--hero-bg);
  backdrop-filter: blur(18px);
  border: 1px solid var(--hero-border);
  border-radius: 24px;
  padding: 1.5rem 1.65rem;
  margin-bottom: 1rem;
  box-shadow: 0 18px 44px rgba(31, 115, 140, 0.11);
  animation: bu-panel-in 0.5s cubic-bezier(.22,.9,.28,1) both;
}}
.bu-hero h1, .bu-hero h2 {{
  margin: 0.35rem 0 0;
  font-family: "Outfit", "Noto Sans SC", sans-serif;
  font-size: var(--font-hero);
  font-weight: 700;
  color: var(--accent-title);
  line-height: 1.35;
  letter-spacing: -0.01em;
}}
.bu-hero p {{ margin: 0.55rem 0 0; color: var(--text-soft); line-height: 1.55; }}
.bu-hero.bu-login {{ margin-top: 0.25rem; }}
@keyframes bu-panel-in {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* Buttons — high specificity so Streamlit light chrome cannot win in dark mode */
.stApp .stButton > button,
.stApp .stDownloadButton > button,
.stApp button[data-testid="baseButton-secondary"],
.stApp button[data-testid="baseButton-primary"] {{
  border-radius: 999px !important;
  border: 1px solid var(--field-border) !important;
  background: var(--btn-bg) !important;
  background-color: var(--btn-bg) !important;
  color: var(--btn-fg) !important;
  font-weight: 600 !important;
  font-size: var(--font-base) !important;
  box-shadow: 0 8px 20px rgba(31, 115, 140, 0.12) !important;
}}
.stApp .stButton > button *,
.stApp .stDownloadButton > button *,
.stApp button[data-testid="baseButton-secondary"] *,
.stApp button[data-testid="baseButton-primary"] * {{
  color: var(--btn-fg) !important;
  -webkit-text-fill-color: var(--btn-fg) !important;
}}
.stApp .stButton > button[kind="primary"],
.stApp .stDownloadButton > button[kind="primary"],
.stApp button[data-testid="baseButton-primary"] {{
  background: linear-gradient(135deg, #1f738c, #2f9eb8) !important;
  background-color: #2f9eb8 !important;
  color: #f7fcff !important;
  border: none !important;
}}
.stApp .stButton > button[kind="primary"] *,
.stApp .stDownloadButton > button[kind="primary"] *,
.stApp button[data-testid="baseButton-primary"] * {{
  color: #f7fcff !important;
  -webkit-text-fill-color: #f7fcff !important;
}}

/* Expander headers — cover nested/open/closed + Streamlit light chrome */
.stApp [data-testid="stExpander"],
.stApp [data-testid="stExpander"] > details,
.stApp [data-testid="stExpander"] details,
.stApp .streamlit-expanderContent,
.stApp .streamlit-expanderHeader,
.stApp [data-testid="stExpander"] summary,
.stApp [data-testid="stExpander"] summary > div,
.stApp [data-testid="stExpander"] summary > div > div {{
  background: var(--exp-bg) !important;
  background-color: var(--exp-bg) !important;
  background-image: none !important;
  border-color: var(--cream-border) !important;
  color: var(--exp-fg) !important;
}}
.stApp [data-testid="stExpander"] {{
  border: 1px solid var(--cream-border) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
}}
.stApp [data-testid="stExpander"] summary,
.stApp [data-testid="stExpander"] summary *,
.stApp [data-testid="stExpander"] summary p,
.stApp [data-testid="stExpander"] summary span,
.stApp [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"],
.stApp [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] *,
.stApp .streamlit-expanderHeader,
.stApp .streamlit-expanderHeader *,
.stApp .streamlit-expanderHeader p,
.stApp .streamlit-expanderHeader span {{
  color: var(--exp-fg) !important;
  -webkit-text-fill-color: var(--exp-fg) !important;
  fill: var(--exp-fg) !important;
  background: transparent !important;
  background-color: transparent !important;
}}
.stApp [data-testid="stExpander"] summary {{
  background: var(--exp-bg) !important;
  background-color: var(--exp-bg) !important;
  list-style: none !important;
}}
.stApp [data-testid="stExpander"] summary svg,
.stApp [data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"],
.stApp [data-testid="stExpander"] summary [data-testid="stExpanderIcon"] {{
  color: var(--exp-fg) !important;
  fill: var(--exp-fg) !important;
  stroke: var(--exp-fg) !important;
}}
.stApp [data-testid="stExpander"] [data-testid="stExpanderDetails"],
.stApp .streamlit-expanderContent {{
  background: var(--exp-bg) !important;
  background-color: var(--exp-bg) !important;
  color: var(--text) !important;
  border-top: 1px solid var(--cream-border) !important;
}}

/* File uploader — dropzone only; never paint nested button chrome black */
.stApp [data-testid="stFileUploader"] section,
.stApp [data-testid="stFileUploaderDropzone"] {{
  background: var(--cream) !important;
  background-color: var(--cream) !important;
  border-color: var(--cream-border) !important;
  color: var(--text) !important;
}}
.stApp [data-testid="stFileUploaderDropzone"] small,
.stApp [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"],
.stApp [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] * {{
  color: var(--text-soft) !important;
  -webkit-text-fill-color: var(--text-soft) !important;
  background: transparent !important;
  background-color: transparent !important;
}}
.stApp [data-testid="stFileUploader"] button,
.stApp [data-testid="stFileUploaderDropzone"] button {{
  background: linear-gradient(135deg, #1f738c, #2f9eb8) !important;
  background-color: #2f9eb8 !important;
  background-image: linear-gradient(135deg, #1f738c, #2f9eb8) !important;
  color: #f7fcff !important;
  border: none !important;
  box-shadow: none !important;
}}
.stApp [data-testid="stFileUploader"] button *,
.stApp [data-testid="stFileUploaderDropzone"] button *,
.stApp [data-testid="stFileUploader"] button span,
.stApp [data-testid="stFileUploader"] button div,
.stApp [data-testid="stFileUploader"] button p {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  color: #f7fcff !important;
  -webkit-text-fill-color: #f7fcff !important;
  box-shadow: none !important;
  border: none !important;
}}
.stApp [data-testid="stFileUploader"] button svg {{
  fill: #f7fcff !important;
  color: #f7fcff !important;
  background: transparent !important;
}}

[data-testid="stChatMessage"] {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}}

/* Chat footer — Streamlit theme.toml is light-only; paint bottom chrome ourselves */
[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"],
section[data-testid="stBottom"],
.stApp [data-testid="stBottomBlockContainer"] {{
  background: var(--sky-bg) !important;
  background-color: var(--sky-bg) !important;
  background-image: none !important;
  border-top: 1px solid var(--cream-border) !important;
  color: var(--text) !important;
}}
[data-testid="stBottomBlockContainer"] > div,
[data-testid="stBottomBlockContainer"] [data-testid="stChatInput"],
[data-testid="stBottom"] > div {{
  background: transparent !important;
  background-color: transparent !important;
}}
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] {{
  background: transparent !important;
}}
.stApp [data-testid="stVerticalBlockBorderWrapper"] {{
  background: transparent !important;
}}

[data-testid="stChatInput"] {{
  background: transparent !important;
  color: var(--field-text) !important;
}}
[data-testid="stChatInput"] > div {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] [data-baseweb="base-input"],
[data-testid="stChatInput"] [data-baseweb="textarea"] {{
  background: var(--field-bg) !important;
  background-color: var(--field-bg) !important;
  backdrop-filter: blur(18px) !important;
  color: var(--field-text) !important;
  -webkit-text-fill-color: var(--field-text) !important;
  font-size: var(--font-base) !important;
  border: 1px solid var(--field-border) !important;
  border-radius: 999px !important;
  box-shadow: 0 14px 36px rgba(31, 115, 140, 0.13) !important;
  padding: 0.75rem 1.2rem !important;
  transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
  color: var(--text-soft) !important;
  -webkit-text-fill-color: var(--text-soft) !important;
  opacity: 0.85 !important;
}}
[data-testid="stChatInput"] textarea:focus {{
  border-color: rgba(47, 158, 184, 0.55) !important;
  box-shadow: 0 16px 40px rgba(31, 115, 140, 0.18) !important;
}}
[data-testid="stChatInput"] button {{
  background: linear-gradient(135deg, #1f738c, #2f9eb8) !important;
  color: #f7fcff !important;
  border: none !important;
}}
[data-testid="stChatInput"] button svg {{
  fill: #f7fcff !important;
  color: #f7fcff !important;
}}

/* Scope body text; avoid styling button or expander inner paragraphs. */
h1, h2, h3, label,
[data-testid="stMarkdownContainer"] > p,
[data-testid="stCaptionContainer"],
.stCaption {{
  color: var(--text);
}}

[data-testid="stTextInput"] > div,
[data-testid="stTextInput"] [data-baseweb="base-input"],
[data-testid="stTextArea"] > div,
[data-testid="stTextArea"] [data-baseweb="base-input"],
[data-testid="stNumberInput"] > div,
[data-testid="stNumberInput"] [data-baseweb="base-input"],
[data-testid="stDateInput"] > div,
[data-testid="stDateInput"] [data-baseweb="base-input"],
[data-testid="stSelectbox"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
  background: var(--field-bg) !important;
  background-color: var(--field-bg) !important;
  border-color: var(--field-border) !important;
  color: var(--field-text) !important;
  box-shadow: none !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {{
  background: transparent !important;
  background-color: transparent !important;
  border: 1px solid var(--field-border) !important;
  border-radius: 14px !important;
  color: var(--field-text) !important;
  -webkit-text-fill-color: var(--field-text) !important;
  box-shadow: none !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stDateInput"] input:focus {{
  border-color: rgba(47, 158, 184, 0.55) !important;
  box-shadow: 0 8px 22px rgba(31, 115, 140, 0.14) !important;
}}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stDateInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label,
.stApp label,
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] * {{
  color: var(--text) !important;
  -webkit-text-fill-color: var(--text) !important;
}}
[data-baseweb="tab"] {{
  font-weight: 650 !important;
  color: var(--text) !important;
}}

.bu-workspace-head h3 {{ color: var(--accent-title) !important; }}
.bu-workspace-head p {{ color: var(--text-soft) !important; }}

/* Changelog / st.dialog — opaque surface so dark-mode text stays readable */
div[data-testid="stModal"],
div[data-testid="stDialog"],
div[role="dialog"],
section[data-testid="stModal"] {{
  color: var(--text) !important;
}}
div[data-testid="stModal"] > div,
div[data-testid="stDialog"] > div,
div[role="dialog"] > div,
section[data-testid="stModal"] > div {{
  background: var(--exp-bg) !important;
  background-color: var(--exp-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--cream-border) !important;
  opacity: 1 !important;
  backdrop-filter: none !important;
}}
div[data-testid="stModal"] [data-testid="stMarkdownContainer"],
div[data-testid="stModal"] [data-testid="stMarkdownContainer"] p,
div[data-testid="stModal"] [data-testid="stCaptionContainer"],
div[data-testid="stModal"] [data-testid="stCaptionContainer"] *,
div[role="dialog"] [data-testid="stMarkdownContainer"],
div[role="dialog"] [data-testid="stMarkdownContainer"] p,
div[role="dialog"] [data-testid="stCaptionContainer"],
div[role="dialog"] [data-testid="stCaptionContainer"] * {{
  color: var(--text) !important;
  -webkit-text-fill-color: var(--text) !important;
}}
div[data-testid="stModal"] h1,
div[data-testid="stModal"] h2,
div[data-testid="stModal"] h3,
div[role="dialog"] h1,
div[role="dialog"] h2,
div[role="dialog"] h3 {{
  color: var(--accent-title) !important;
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
    safe_st_html(
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
    "inject_chunk_recovery",
    "inject_ui_phase",
    "render_agent_bubble",
    "render_fun_home",
    "render_login_header",
    "safe_st_html",
]

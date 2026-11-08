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
    """Auto cache-bust reload when Streamlit widget JS chunks fail to load.

    chat_input / uploaders often surface ``Failed to fetch dynamically imported
    module`` after Cloud sleep or redeploy. One soft recovery per tab load;
    also watches the DOM for the error text widgets paint into the page.
    """
    if st.session_state.get("_bubu_chunk_guard_injected"):
        return
    st.session_state._bubu_chunk_guard_injected = True
    script = """
<script>
(function () {
  if (window.__bubuChunkGuard) return;
  window.__bubuChunkGuard = true;
  var recovering = false;
  function isChunkFail(err) {
    var s = String((err && err.message) || err || "");
    return /Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module/i.test(s);
  }
  function recover() {
    if (recovering) return;
    try {
      // At most one auto-reload per 3 minutes — looping reload looked like endless spinner.
      var last = Number(localStorage.getItem("bubu_chunk_ts") || "0");
      if (Date.now() - last < 180000) return;
      if (sessionStorage.getItem("bubu_chunk_reload") === "1") return;
      recovering = true;
      sessionStorage.setItem("bubu_chunk_reload", "1");
      localStorage.setItem("bubu_chunk_ts", String(Date.now()));
      try {
        if (window.caches && caches.keys) {
          caches.keys().then(function (keys) {
            keys.forEach(function (k) { caches.delete(k); });
          }).catch(function () {});
        }
      } catch (e) {}
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
    if (isChunkFail(ev && (ev.error || ev.message))) recover();
  }, true);
  var checks = 0;
  var timer = setInterval(function () {
    checks += 1;
    try {
      var body = document.body ? (document.body.innerText || "") : "";
      if (body.indexOf("Failed to fetch dynamically imported module") >= 0) recover();
    } catch (e) {}
    if (checks > 45) clearInterval(timer);
  }, 1200);
  setTimeout(function () {
    try { sessionStorage.removeItem("bubu_chunk_reload"); } catch (e) {}
  }, 45000);
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
        # UI-09 dark surface tokens
        vars_css = """
  --sky: #2F9EB8;
  --sky-deep: #2F9EB8;
  --sky-bg: #12181C;
  --cream: #1C262C;
  --cream-hover: #243038;
  --cream-border: #2C3C46;
  --text: #E7EEF2;
  --text-soft: #A9B8C2;
  --field-bg: #1C262C;
  --field-text: #E7EEF2;
  --field-border: #2C3C46;
  --app-bg: #12181C;
  --sidebar-bg: #12181C;
  --card-bg: #1C262C;
  --accent-title: #2F9EB8;
  --hero-bg: #1C262C;
  --hero-border: #2C3C46;
"""
    else:
        # UI-01 / UI-02 quiet light surfaces
        vars_css = """
  --sky: #2F9EB8;
  --sky-deep: #2F9EB8;
  --sky-bg: #F4F7F8;
  --cream: #FFFFFF;
  --cream-hover: #F4F7F8;
  --cream-border: #E3EEF2;
  --text: #1C2B33;
  --text-soft: #5C6F7A;
  --field-bg: #FFFFFF;
  --field-text: #1C2B33;
  --field-border: #E3EEF2;
  --app-bg: #F4F7F8;
  --sidebar-bg: #FFFFFF;
  --card-bg: #FFFFFF;
  --accent-title: #1C2B33;
  --hero-bg: #FFFFFF;
  --hero-border: #E3EEF2;
"""

    btn_bg = "#2F9EB8" if not is_dark else "#2F9EB8"
    btn_fg = "#FFFFFF"
    exp_bg = "#1C262C" if is_dark else "#FFFFFF"
    exp_fg = "#E7EEF2" if is_dark else "#1C2B33"
    # Prefer markdown for CSS (lighter than st.html). No per-rerun JS here —
    # timers/DOM moves were fighting chat_input chunk loads on weak networks.
    st.markdown(
        f"""
<style>
/* System fonts only — Google Fonts often hang on campus / CN networks */
:root {{
{vars_css}
  --font-base: {fs};
  --font-hero: {hero};
  --btn-bg: {btn_bg};
  --btn-fg: {btn_fg};
  --exp-bg: {exp_bg};
  --exp-fg: {exp_fg};
  --font-ui: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC",
    -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}

.stApp {{
  background: var(--app-bg) !important;
  background-color: var(--sky-bg) !important;
  color: var(--text);
  font-family: var(--font-ui);
  font-size: 14px;
  line-height: 1.5;
  letter-spacing: 0.01em;
}}
.stApp [data-testid="stAppViewContainer"],
.stApp [data-testid="stAppViewContainer"] > .main,
.stApp section.main {{
  background: var(--sky-bg) !important;
  background-color: var(--sky-bg) !important;
}}
.stApp .main .block-container {{
  background: transparent !important;
  max-width: 760px !important;
  padding-top: 1.25rem !important;
  padding-left: 24px !important;
  padding-right: 24px !important;
  padding-bottom: 2rem !important;
}}
/* Login: single centered card (UI-08) — hide dual-rail */
.stApp:has(.bu-login-shell) section[data-testid="stSidebar"],
.stApp:has(.bu-login-shell) [data-testid="stSidebarCollapsedControl"],
.stApp:has(.bu-login-shell) [data-testid="collapsedControl"] {{
  display: none !important;
}}
.stApp:has(.bu-login-shell) .main .block-container {{
  max-width: 420px !important;
  padding-top: 8vh !important;
  background: var(--card-bg) !important;
  border: 1px solid var(--cream-border) !important;
  border-radius: 12px !important;
  padding-left: 20px !important;
  padding-right: 20px !important;
  padding-bottom: 20px !important;
  box-shadow: none !important;
}}
.bu-login-shell {{
  display: none;
}}
.bu-login-shell .bu-hero {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 0 0.75rem !important;
  margin: 0 !important;
}}
.bu-login-shell .bu-hero h2 {{
  font-size: 22px !important;
  font-weight: 600 !important;
  color: var(--text) !important;
}}
.bu-login-shell .bu-hero p {{
  font-size: 14px !important;
  color: var(--text-soft) !important;
}}
section[data-testid="stSidebar"] {{
  background: var(--sidebar-bg) !important;
  border-right: 1px solid var(--cream-border) !important;
  box-shadow: none !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
  width: 272px !important;
}}
.bu-nav-brand {{
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin: 0.25rem 0 0.75rem;
}}
.bu-nav-credit {{
  font-size: 12px;
  color: var(--text-soft);
  margin-top: 0.75rem;
}}
.bu-account-plain {{
  font-size: 13px;
  color: var(--text);
  margin: 0.35rem 0;
  overflow-wrap: anywhere;
}}
@media (max-width: 768px) {{
  .stApp .main .block-container {{
    padding-left: 16px !important;
    padding-right: 16px !important;
  }}
  section[data-testid="stSidebar"] > div:first-child {{
    width: min(100vw, 100%) !important;
  }}
}}

.bu-workspace-head {{
  margin: 0 0 1rem;
  padding: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}}
.bu-workspace-head h3 {{
  margin: 0;
  font-family: var(--font-ui);
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.01em;
}}
.bu-workspace-head p {{
  margin: 0.35rem 0 0;
  color: var(--text-soft);
  font-size: 14px;
  line-height: 1.5;
}}
.bu-chat-guide {{
  margin: 2.5rem auto 1.5rem;
  text-align: center;
  max-width: 28rem;
}}
.bu-chat-guide .bu-chat-guide-name {{
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
}}
.bu-chat-guide .bu-chat-guide-hint {{
  margin: 0.5rem 0 0;
  font-size: 14px;
  color: var(--text-soft);
  line-height: 1.5;
}}
.bu-card {{
  background: var(--card-bg);
  border: 1px solid var(--cream-border);
  border-radius: 12px;
  padding: 16px 20px;
  margin: 0 0 16px;
}}
.bu-upload-box {{
  border: 1.5px dashed var(--cream-border);
  border-radius: 12px;
  padding: 16px;
  background: var(--card-bg);
  margin: 0 0 12px;
}}
.bu-upload-box p {{
  margin: 0 0 0.35rem;
  color: var(--text-soft);
  font-size: 12px;
}}

header[data-testid="stHeader"] {{
  background: transparent;
  pointer-events: none;
}}
header[data-testid="stHeader"] > div {{
  pointer-events: auto;
}}

[data-testid="stSidebar"] {{
  background: var(--sidebar-bg) !important;
  border-right: 1px solid var(--cream-border) !important;
  box-shadow: none !important;
  overflow-x: hidden !important;
  color: var(--text);
}}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
  padding: 16px 12px 20px !important;
}}
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
  font-size: 12px !important;
}}
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
/* Nav radio: accent only on selected (UI-02 / UI-03) */
[data-testid="stSidebar"] [role="radiogroup"] label {{
  border-radius: 10px !important;
  padding: 0.35rem 0.55rem !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"],
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
  background: color-mix(in srgb, var(--sky) 14%, transparent) !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] p,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p,
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] span,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) span {{
  color: var(--sky) !important;
  font-weight: 600 !important;
}}

.bu-hero {{
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0 0 0.75rem;
  margin-bottom: 0.5rem;
  box-shadow: none;
}}
.bu-hero h1, .bu-hero h2 {{
  margin: 0;
  font-family: var(--font-ui);
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.35;
  letter-spacing: -0.01em;
}}
.bu-hero p {{ margin: 0.45rem 0 0; color: var(--text-soft); font-size: 14px; line-height: 1.5; }}
.bu-hero.bu-login {{ margin-top: 0; }}

/* Buttons — one primary accent; height 40px / radius 10px (UI-13) */
.stApp .stButton > button,
.stApp .stDownloadButton > button,
.stApp button[data-testid="baseButton-secondary"],
.stApp button[data-testid="baseButton-primary"] {{
  border-radius: 10px !important;
  min-height: 40px !important;
  height: 40px !important;
  border: 1px solid var(--field-border) !important;
  background: var(--card-bg) !important;
  background-color: var(--card-bg) !important;
  color: var(--text) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  box-shadow: none !important;
}}
.stApp .stButton > button *,
.stApp .stDownloadButton > button *,
.stApp button[data-testid="baseButton-secondary"] *,
.stApp button[data-testid="baseButton-primary"] * {{
  color: inherit !important;
  -webkit-text-fill-color: currentColor !important;
}}
.stApp .stButton > button[kind="primary"],
.stApp .stDownloadButton > button[kind="primary"],
.stApp button[data-testid="baseButton-primary"] {{
  background: #2F9EB8 !important;
  background-color: #2F9EB8 !important;
  color: #FFFFFF !important;
  border: none !important;
}}
.stApp .stButton > button[kind="primary"] *,
.stApp .stDownloadButton > button[kind="primary"] *,
.stApp button[data-testid="baseButton-primary"] * {{
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
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
.stApp [data-testid="stFileUploaderDropzone"] {{
  border: 1.5px dashed var(--cream-border) !important;
  border-radius: 12px !important;
}}
.stApp [data-testid="stFileUploader"] button,
.stApp [data-testid="stFileUploaderDropzone"] button {{
  background: #2F9EB8 !important;
  background-color: #2F9EB8 !important;
  background-image: none !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 10px !important;
  min-height: 40px !important;
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
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  box-shadow: none !important;
  border: none !important;
}}
.stApp [data-testid="stFileUploader"] button svg {{
  fill: #FFFFFF !important;
  color: #FFFFFF !important;
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
  background: var(--sky-bg) !important;
}}
.stApp [data-testid="stVerticalBlockBorderWrapper"] {{
  background: transparent !important;
}}
[data-testid="stBottomBlockContainer"] {{
  padding-bottom: 12px !important;
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
  color: var(--field-text) !important;
  -webkit-text-fill-color: var(--field-text) !important;
  font-size: 14px !important;
  border: 1px solid var(--field-border) !important;
  border-radius: 24px !important;
  min-height: 48px !important;
  box-shadow: none !important;
  padding: 0.7rem 1.1rem !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
  color: var(--text-soft) !important;
  -webkit-text-fill-color: var(--text-soft) !important;
  opacity: 0.85 !important;
}}
[data-testid="stChatInput"] textarea:focus {{
  border-color: #2F9EB8 !important;
  box-shadow: 0 0 0 2px color-mix(in srgb, #2F9EB8 25%, transparent) !important;
}}
[data-testid="stChatInput"] button {{
  background: #2F9EB8 !important;
  color: #FFFFFF !important;
  border: none !important;
}}
[data-testid="stChatInput"] button svg {{
  fill: #FFFFFF !important;
  color: #FFFFFF !important;
}}

/* Scope body text; avoid styling button or expander inner paragraphs. */
h1, h2, h3, label,
[data-testid="stMarkdownContainer"] > p,
[data-testid="stCaptionContainer"],
.stCaption {{
  color: var(--text);
}}

/* Form fields — solid fill + teal border so boxes stay visible on sky bg */
[data-testid="stTextInput"] > div > div,
[data-testid="stTextInput"] [data-baseweb="base-input"],
[data-testid="stTextArea"] > div > div,
[data-testid="stTextArea"] [data-baseweb="base-input"],
[data-testid="stNumberInput"] > div > div,
[data-testid="stNumberInput"] [data-baseweb="base-input"],
[data-testid="stDateInput"] > div > div,
[data-testid="stDateInput"] [data-baseweb="base-input"],
[data-testid="stSelectbox"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
  background: var(--field-bg) !important;
  background-color: var(--field-bg) !important;
  border: 1px solid var(--field-border) !important;
  border-color: var(--field-border) !important;
  border-radius: 10px !important;
  color: var(--field-text) !important;
  box-shadow: none !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {{
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  border-radius: 10px !important;
  color: var(--field-text) !important;
  -webkit-text-fill-color: var(--field-text) !important;
  box-shadow: none !important;
}}
[data-testid="stTextInput"] [data-baseweb="base-input"]:focus-within,
[data-testid="stTextArea"] [data-baseweb="base-input"]:focus-within,
[data-testid="stDateInput"] [data-baseweb="base-input"]:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {{
  border-color: #2F9EB8 !important;
  box-shadow: 0 0 0 2px color-mix(in srgb, #2F9EB8 25%, transparent) !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stDateInput"] input:focus {{
  outline: none !important;
  box-shadow: none !important;
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

/* Cloud host chrome: Favorite/star is not a BuBu control — hide to avoid confusion */
header[data-testid="stHeader"] button[aria-label*="Favorite" i],
header[data-testid="stHeader"] button[aria-label*="Favourite" i],
header[data-testid="stHeader"] button[title*="Favorite" i],
header[data-testid="stHeader"] button[title*="Favourite" i],
header[data-testid="stHeader"] a[aria-label*="Favorite" i],
header[data-testid="stHeader"] a[title*="Favorite" i] {{
  display: none !important;
}}

@media (max-width: 768px) {{
  /* UI-10: drawer covers stage; main keeps 16px gutters (set above) */
  section[data-testid="stSidebar"] {{
    z-index: 1000002 !important;
  }}
}}
</style>
        """,
        unsafe_allow_html=True,
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

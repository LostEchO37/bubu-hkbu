"""Home stage, prompt picker, and chat chrome.

Visual language: soft campus morning light, brand-first hub, glass prompt cards.
Clicks use query params (?wake=1 / ?pick=N + auth) — see app.py.
"""

from __future__ import annotations

import html
from typing import Callable, Literal
from urllib.parse import urlencode

import streamlit as st

from core.i18n import LANG_OPTIONS, t as i18n_t
from core.kaomoji import AGENT_FACE, AGENT_FACE_BURST


def _all_welcome_bodies() -> set[str]:
    return {i18n_t("welcome", code) for _, code in LANG_OPTIONS}  # type: ignore[misc]


UiPhase = Literal["hub", "burst", "chat"]


def inject_ui_phase(phase: UiPhase) -> None:
    """Backward-compatible alias; prefer core.ui.inject_ui_phase."""
    _ensure_shell_css(phase)
    st.markdown(
        f'<div class="ui-phase-marker" data-phase="{phase}"></div>',
        unsafe_allow_html=True,
    )


def _ensure_shell_css(phase: UiPhase | None = None) -> None:
    phase_attr = phase or "chat"
    st.html(
        f"""
<style>
section[data-testid="stMain"]:has(.ui-phase-marker[data-phase="hub"]) .block-container,
section[data-testid="stMain"]:has(.ui-phase-marker[data-phase="burst"]) .block-container {{
  max-width: min(880px, 94vw) !important;
  margin: 0 auto !important;
  padding-top: 1.8vh !important;
}}
section[data-testid="stMain"]:has(.ui-phase-marker[data-phase="hub"]) [data-testid="stBottomBlockContainer"] {{
  opacity: 0 !important;
  pointer-events: none !important;
  max-height: 0 !important;
  overflow: hidden !important;
}}
section[data-testid="stMain"]:has(.ui-phase-marker[data-phase="burst"]) [data-testid="stBottomBlockContainer"],
section[data-testid="stMain"]:has(.ui-phase-marker[data-phase="chat"]) [data-testid="stBottomBlockContainer"] {{
  animation: bu-input-rise 0.55s cubic-bezier(.22,.9,.28,1) 0.28s both;
}}
@keyframes bu-input-rise {{
  from {{ opacity: 0; transform: translateY(14px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
.chat-thread {{
  max-width: 720px;
  margin: 0 auto;
  padding: 0.5rem 0 1.5rem;
}}
.chat-line {{
  margin: 0.85rem 0;
  line-height: 1.65;
  color: var(--text, #243d4a);
  animation: bu-msg-in 0.4s cubic-bezier(.22,.9,.28,1) both;
}}
.chat-line.user {{ text-align: right; }}
.chat-line.user .chat-pill {{
  display: inline-block;
  max-width: 86%;
  text-align: left;
  white-space: pre-wrap;
  background: linear-gradient(145deg, rgba(255,255,255,0.88), rgba(220,240,248,0.72));
  backdrop-filter: blur(14px);
  border-radius: 22px 22px 6px 22px;
  padding: 0.72rem 1.1rem;
  box-shadow: 0 12px 32px rgba(36, 110, 130, 0.11);
  border: 1px solid rgba(255,255,255,0.7);
}}
/* Lead face sits left of the first line — not a floating empty bubble above */
.chat-lead {{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.15rem;
  height: 2.15rem;
  margin-top: 0.2rem;
  border-radius: 999px;
  background: linear-gradient(145deg, #ffffff, #c8e9f4);
  box-shadow: 0 8px 20px rgba(47, 158, 184, 0.22);
  border: 1px solid rgba(255,255,255,0.75);
  font-size: 0.58rem;
  font-weight: 700;
  color: #1f738c;
  letter-spacing: -0.04em;
  line-height: 1;
  user-select: none;
  flex-shrink: 0;
  overflow: hidden;
  white-space: nowrap;
}}
div[data-testid="stHorizontalBlock"]:has(.chat-lead) {{
  gap: 0.55rem !important;
  align-items: flex-start !important;
  margin: 0.75rem 0 0.9rem !important;
  max-width: 720px;
  animation: bu-msg-in 0.4s cubic-bezier(.22,.9,.28,1) both;
}}
div[data-testid="stHorizontalBlock"]:has(.chat-lead)
  > div:last-child [data-testid="stMarkdownContainer"],
div[data-testid="stHorizontalBlock"]:has(.chat-lead)
  > div:last-child [data-testid="stWriteStreamContainer"] {{
  background: rgba(255,255,255,0.42);
  backdrop-filter: blur(12px);
  border-radius: 6px 22px 22px 22px;
  padding: 0.75rem 1.1rem;
  box-shadow: 0 10px 28px rgba(36, 110, 130, 0.08);
  border: 1px solid rgba(255,255,255,0.5);
  line-height: 1.65;
  color: var(--text, #243d4a);
}}
@keyframes bu-msg-in {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@media (prefers-reduced-motion: reduce) {{
  .chat-line,
  div[data-testid="stHorizontalBlock"]:has(.chat-lead),
  section[data-testid="stMain"]:has(.ui-phase-marker) [data-testid="stBottomBlockContainer"] {{
    animation: none !important;
  }}
}}
/* phase={phase_attr} */
</style>
        """,
        width="content",
    )


def _short_label(text: str, n: int = 42) -> str:
    t = text.replace("\n", " ").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def _q(params: dict[str, str]) -> str:
    return "?" + urlencode(params)


def render_agent_bubble(
    hint: str,
    *,
    on_wake: Callable[[], None] | None = None,
    auth_token: str | None = None,
    brand: str = "阿Bu · HKBU",
    title_line1: str = "阿Bu",
    title_line2: str = "同学助手",
    cta: str = "开始聊聊",
    credit: str = "proudly presented by GTSC2066 Group 16",
) -> None:
    """Brand-first hub — CTA opens prompts via ?wake=1&auth=…"""
    del on_wake
    face = html.escape(AGENT_FACE)
    hint_e = html.escape(hint)
    brand_e = html.escape(brand)
    t1 = html.escape(title_line1)
    t2 = html.escape(title_line2)
    cta_e = html.escape(cta)
    credit_e = html.escape(credit)
    wake_params: dict[str, str] = {"wake": "1"}
    if auth_token:
        wake_params["auth"] = auth_token
    wake_href = html.escape(_q(wake_params))

    st.html(
        f"""
<div class="hub-stage-marker" style="display:none"></div>
<style>
.bu-stage {{
  position: relative;
  min-height: 74vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 0.5rem 3.5rem;
  overflow: hidden;
  font-family: "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", sans-serif;
}}
.bu-orb {{
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
  pointer-events: none;
  z-index: 0;
  will-change: transform, opacity;
}}
.bu-orb-a {{
  width: min(460px, 78vw);
  height: min(460px, 78vw);
  left: 50%;
  top: 40%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle at 38% 32%,
    rgba(255,255,255,0.92) 0%,
    rgba(170,224,238,0.5) 42%,
    rgba(90,180,200,0.14) 68%,
    transparent 78%);
  animation: bu-breathe 8s ease-in-out infinite;
}}
.bu-orb-b {{
  width: 200px; height: 200px;
  right: 6%; top: 14%;
  background: radial-gradient(circle, rgba(255,214,170,0.42), transparent 72%);
  animation: bu-drift 12s ease-in-out infinite alternate;
}}
.bu-orb-c {{
  width: 160px; height: 160px;
  left: 8%; bottom: 14%;
  background: radial-gradient(circle, rgba(110,198,220,0.45), transparent 72%);
  animation: bu-drift 10s ease-in-out infinite alternate-reverse;
}}
.bu-ring {{
  position: absolute;
  left: 50%; top: 40%;
  width: min(340px, 58vw);
  height: min(340px, 58vw);
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.35);
  box-shadow: inset 0 0 40px rgba(255,255,255,0.12);
  pointer-events: none;
  z-index: 0;
  animation: bu-ring 10s ease-in-out infinite;
}}
.bu-hero {{
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 38rem;
  animation: bu-rise 0.8s cubic-bezier(.22,.9,.28,1) both;
}}
.bu-kicker {{
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.88rem;
  font-weight: 650;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #3a7a8f;
  margin: 0 0 1.05rem;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.4);
  border: 1px solid rgba(255,255,255,0.55);
  backdrop-filter: blur(10px);
  animation: bu-rise 0.8s cubic-bezier(.22,.9,.28,1) 0.06s both;
}}
.bu-kicker .bu-face {{
  font-size: 1.05rem;
  letter-spacing: 0;
  text-transform: none;
  font-weight: 700;
}}
.bu-title {{
  margin: 0;
  font-family: "Syne", "Noto Sans SC", sans-serif;
  font-weight: 800;
  font-size: clamp(2.55rem, 7.2vw, 3.85rem);
  line-height: 1.05;
  letter-spacing: -0.035em;
  color: #143744;
  text-wrap: balance;
  animation: bu-rise 0.85s cubic-bezier(.22,.9,.28,1) 0.1s both;
}}
.bu-title span {{
  background: linear-gradient(118deg, #176a82 0%, #2a9bb8 48%, #5bc0d4 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}}
.bu-sub {{
  margin: 1.15rem auto 0;
  max-width: 27rem;
  font-size: 1.06rem;
  line-height: 1.62;
  color: #4a6878;
  animation: bu-rise 0.85s cubic-bezier(.22,.9,.28,1) 0.18s both;
}}
a.bu-cta {{
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  margin-top: 1.95rem;
  padding: 1rem 2rem;
  border-radius: 999px;
  text-decoration: none !important;
  color: #f7fcff !important;
  font-weight: 700;
  font-size: 1.08rem;
  letter-spacing: 0.02em;
  overflow: hidden;
  background: linear-gradient(135deg, #1a6f88 0%, #2f9eb8 48%, #56b7cb 100%);
  box-shadow:
    0 18px 42px rgba(31, 115, 140, 0.36),
    inset 0 1px 0 rgba(255,255,255,0.38);
  transition: transform 0.22s ease, box-shadow 0.22s ease, filter 0.22s ease;
  animation: bu-rise 0.9s cubic-bezier(.22,.9,.28,1) 0.28s both, bu-glow 3.8s ease-in-out 1.1s infinite;
}}
a.bu-cta::before {{
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 35%, rgba(255,255,255,0.28) 50%, transparent 65%);
  transform: translateX(-120%);
  animation: bu-shimmer 3.2s ease-in-out 1.6s infinite;
}}
a.bu-cta:hover {{
  transform: translateY(-3px) scale(1.025);
  box-shadow: 0 26px 52px rgba(31, 115, 140, 0.45);
  filter: brightness(1.05);
}}
a.bu-cta .bu-cta-arrow {{
  display: inline-block;
  transition: transform 0.22s ease;
}}
a.bu-cta:hover .bu-cta-arrow {{ transform: translateX(5px); }}
.bu-credit {{
  margin: 1.55rem 0 0;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #6a8a9a;
  opacity: 0.85;
  animation: bu-rise 0.9s cubic-bezier(.22,.9,.28,1) 0.4s both;
}}
@keyframes bu-breathe {{
  0%, 100% {{ transform: translate(-50%, -50%) scale(1); opacity: 0.94; }}
  50% {{ transform: translate(-50%, -53%) scale(1.07); opacity: 1; }}
}}
@keyframes bu-drift {{
  from {{ transform: translate(0, 0); }}
  to {{ transform: translate(20px, -16px); }}
}}
@keyframes bu-ring {{
  0%, 100% {{ opacity: 0.35; transform: translate(-50%, -50%) scale(1); }}
  50% {{ opacity: 0.65; transform: translate(-50%, -50%) scale(1.04); }}
}}
@keyframes bu-rise {{
  from {{ opacity: 0; transform: translateY(20px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes bu-glow {{
  0%, 100% {{ box-shadow: 0 18px 42px rgba(31, 115, 140, 0.36), inset 0 1px 0 rgba(255,255,255,0.38); }}
  50% {{ box-shadow: 0 22px 54px rgba(31, 115, 140, 0.5), inset 0 1px 0 rgba(255,255,255,0.42); }}
}}
@keyframes bu-shimmer {{
  0% {{ transform: translateX(-120%); }}
  40%, 100% {{ transform: translateX(120%); }}
}}
@media (prefers-reduced-motion: reduce) {{
  .bu-orb, .bu-ring, .bu-hero, .bu-kicker, .bu-title, .bu-sub, a.bu-cta, .bu-credit {{
    animation: none !important;
  }}
  a.bu-cta::before {{ display: none; }}
}}
</style>
<div class="bu-stage">
  <div class="bu-orb bu-orb-a" aria-hidden="true"></div>
  <div class="bu-orb bu-orb-b" aria-hidden="true"></div>
  <div class="bu-orb bu-orb-c" aria-hidden="true"></div>
  <div class="bu-ring" aria-hidden="true"></div>
  <div class="bu-hero">
    <p class="bu-kicker"><span class="bu-face">{face}</span> {brand_e}</p>
    <h1 class="bu-title">{t1}<br/><span>{t2}</span></h1>
    <p class="bu-sub">{hint_e}</p>
    <a class="bu-cta bu-blob" href="{wake_href}" title="{hint_e}">
      {cta_e} <span class="bu-cta-arrow">→</span>
    </a>
    <p class="bu-credit">{credit_e}</p>
  </div>
</div>
        """,
        width="stretch",
    )


def render_mini_prompt_bubbles(
    prompts: list[str],
    *,
    plan_label: str | None = None,
    hint: str = "Pick a topic to start chatting",
    auth_token: str | None = None,
) -> None:
    """Staggered glass prompt cards — clicks via ?pick=N&auth=…"""
    labels = list(prompts)
    if plan_label:
        labels.append(plan_label)

    cards = []
    for i, label in enumerate(labels[:5]):
        pick_params: dict[str, str] = {"pick": str(i)}
        if auth_token:
            pick_params["auth"] = auth_token
        href = html.escape(_q(pick_params))
        delay = 0.05 + i * 0.065
        num = f"{i + 1:02d}"
        cards.append(
            f"""
<a class="bu-prompt bu-cell" href="{href}" title="{html.escape(label)}"
   style="animation-delay:{delay}s">
  <span class="bu-prompt-num">{num}</span>
  <span class="bu-prompt-text">{html.escape(_short_label(label, 52))}</span>
  <span class="bu-prompt-go">→</span>
</a>
            """.strip()
        )

    core = html.escape(AGENT_FACE_BURST)
    hint_e = html.escape(hint)
    cards_html = "\n".join(cards)

    st.html(
        f"""
<div class="mitosis-stage-marker" style="display:none"></div>
<style>
.bu-pick {{
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  padding: 1.6rem 0.25rem 1.4rem;
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
}}
.bu-pick-head {{
  text-align: center;
  margin-bottom: 1.4rem;
  animation: bu-rise 0.5s cubic-bezier(.22,.9,.28,1) both;
}}
.bu-pick-face {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  margin-bottom: 0.7rem;
  background: linear-gradient(145deg, #ffffff, #c5e8f3);
  box-shadow: 0 12px 30px rgba(47, 158, 184, 0.28);
  font-weight: 700;
  color: #1f738c;
  font-size: 0.85rem;
  animation: bu-face-pulse 2.8s ease-in-out infinite;
}}
.bu-pick-hint {{
  margin: 0;
  color: #4a6878;
  font-size: 1.06rem;
  font-weight: 500;
}}
.bu-pick-list {{
  display: flex;
  flex-direction: column;
  gap: 0.72rem;
}}
a.bu-prompt {{
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.95rem;
  padding: 1.05rem 1.2rem;
  border-radius: 18px;
  text-decoration: none !important;
  color: #1f4554 !important;
  background: rgba(255,255,255,0.58);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.72);
  border-left: 3px solid rgba(47, 158, 184, 0.55);
  box-shadow: 0 12px 32px rgba(36, 110, 130, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, border-color 0.2s ease;
  animation: bu-card-in 0.5s cubic-bezier(.22,.9,.28,1) both;
}}
a.bu-prompt:hover {{
  transform: translateY(-3px) translateX(5px);
  background: rgba(255,255,255,0.88);
  border-color: rgba(86, 183, 203, 0.6);
  border-left-color: #2f9eb8;
  box-shadow: 0 18px 42px rgba(36, 110, 130, 0.16);
}}
a.bu-prompt:hover .bu-prompt-go {{
  transform: translateX(4px);
  color: #1f738c;
}}
.bu-prompt-num {{
  font-family: "Syne", sans-serif;
  font-weight: 700;
  font-size: 0.82rem;
  letter-spacing: 0.05em;
  color: #5a9bb0;
  min-width: 1.6rem;
}}
.bu-prompt-text {{
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.45;
  text-align: left;
}}
.bu-prompt-go {{
  font-size: 1.15rem;
  color: #7aa8b8;
  transition: transform 0.2s ease, color 0.2s ease;
}}
@keyframes bu-card-in {{
  from {{ opacity: 0; transform: translateY(14px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes bu-rise {{
  from {{ opacity: 0; transform: translateY(14px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes bu-face-pulse {{
  0%, 100% {{ transform: scale(1); box-shadow: 0 12px 30px rgba(47, 158, 184, 0.28); }}
  50% {{ transform: scale(1.04); box-shadow: 0 14px 36px rgba(47, 158, 184, 0.36); }}
}}
@media (prefers-reduced-motion: reduce) {{
  .bu-pick-head, a.bu-prompt, .bu-pick-face {{ animation: none !important; }}
}}
</style>
<div class="bu-pick">
  <div class="bu-pick-head">
    <div class="bu-pick-face" title="{core}">{core}</div>
    <p class="bu-pick-hint">{hint_e}</p>
  </div>
  <div class="bu-pick-list">
    {cards_html}
  </div>
</div>
        """,
        width="stretch",
    )


def _render_chat_lead() -> None:
    face = html.escape(AGENT_FACE)
    st.markdown(
        f'<div class="chat-lead" aria-hidden="true" title="{face}">{face}</div>',
        unsafe_allow_html=True,
    )


def render_ai_turn(content: str) -> None:
    """Assistant row: face lead on the left, markdown body on the right."""
    lead, body = st.columns([0.09, 0.91], gap="small")
    with lead:
        _render_chat_lead()
    with body:
        st.markdown(content)


def begin_ai_stream():
    """Open lead + body columns for streaming; returns the body column context."""
    lead, body = st.columns([0.09, 0.91], gap="small")
    with lead:
        _render_chat_lead()
    return body


def render_chat_thread(messages: list[dict[str, str]]) -> None:
    _ensure_shell_css("chat")
    welcomes = _all_welcome_bodies()
    has_user = any(m.get("role") == "user" for m in messages)
    st.markdown('<div class="chat-thread">', unsafe_allow_html=True)
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "assistant" and has_user and content in welcomes:
            continue
        if role == "user":
            st.markdown(
                f'<div class="chat-line user"><span class="chat-pill">{html.escape(content)}</span></div>',
                unsafe_allow_html=True,
            )
        elif role == "assistant":
            render_ai_turn(content)
    st.markdown("</div>", unsafe_allow_html=True)

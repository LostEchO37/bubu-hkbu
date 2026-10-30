"""HKBU Student Assistant — Streamlit chatbot."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass


def load_server_secrets() -> None:
    """API keys live on the server only — never shown in the public UI."""
    try:
        for key in (
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "OPENAI_MODEL",
            "OPENAI_VISION_MODEL",
            "LLM_PROVIDER",
        ):
            if key in st.secrets:
                os.environ[key] = str(st.secrets[key])
    except Exception:
        pass
    if not os.environ.get("LLM_PROVIDER"):
        os.environ["LLM_PROVIDER"] = "hkbu"

from core.agent import chat_completion_stream, suggest_study_plan
from core.app_settings import AppSettings
from core.auth import get_user_by_id, load_session, login_user, register_user, save_session
from core.session_token import make_auth_token, verify_auth_token
from core.database import init_db
from core.i18n import LANG_OPTIONS, Lang, t
from core.profile import (
    EmailSnippet,
    StudentProfile,
    TaskItem,
    analyze_timetable,
    dumps_profile,
    loads_profile,
    week_grid_html,
)
from core.timetable_vision import parse_timetable_from_image
from core.mail_vision import draft_reply_from_email_image, format_draft_for_chat
from core.extension_pack import extension_zip_bytes
from core.home_agent import (
    begin_ai_stream,
    render_agent_bubble,
    render_chat_thread,
    render_mini_prompt_bubbles,
)
from core.identity import PROJECT_CREDIT, bot_nick
from core.today import pulse_html
from core.ui import inject_bu_theme, inject_ui_phase, render_login_header

# Bump when chat UI flow changes — forces one-time hub reset for logged-in sessions.
_UI_REVISION = 20

st.set_page_config(
    page_title="阿Bu · HKBU Student Assistant",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_lang() -> Lang:
    if "ui_lang" not in st.session_state:
        st.session_state.ui_lang = "zh-CN"
    return st.session_state.ui_lang  # type: ignore[return-value]


def reset_to_hub(lang: Lang, *, persist: bool = True, clear_burst: bool = True) -> None:
    """Welcome-only chat + bubble hub (clears stuck history)."""
    st.session_state.messages = default_welcome(lang)
    if clear_burst:
        st.session_state.agent_burst = False
    # Keep signed auth token so HTML bubble <a href> reloads stay logged in.
    # Drop one-shot navigation flags only.
    try:
        auth = st.query_params.get("auth")
        for key in ("wake", "pick", "fab"):
            if key in st.query_params:
                del st.query_params[key]
        if auth:
            st.query_params["auth"] = auth
    except Exception:
        pass
    if persist and st.session_state.get("user_id"):
        persist_user_data()


def restore_auth_from_query() -> None:
    """HTML bubble links full-reload the page (new Streamlit session). Rehydrate user."""
    if st.session_state.get("user_id"):
        return
    uid = verify_auth_token(st.query_params.get("auth"))
    if not uid:
        return
    info = get_user_by_id(uid)
    if not info:
        return
    username, display = info
    st.session_state.user_id = uid
    st.session_state.account_username = username
    st.session_state.display_name = display
    st.session_state._db_loaded = False


def ensure_auth_query_param() -> str | None:
    """Keep auth= in the URL while logged in so bubble links can append actions."""
    uid = st.session_state.get("user_id")
    if not uid:
        return None
    uid_i = int(uid)
    existing = st.query_params.get("auth")
    # Reuse valid token — minting a new one every run would change the URL and loop-rerun.
    if existing and verify_auth_token(existing) == uid_i:
        return existing
    token = make_auth_token(uid_i)
    try:
        st.query_params["auth"] = token
    except Exception:
        pass
    return token


def capture_nav_intents() -> None:
    """Read wake/pick/fab before hub reset can interfere; apply after session hydrate."""
    if st.query_params.get("wake") == "1":
        st.session_state._wake_intent = True
        try:
            del st.query_params["wake"]
        except Exception:
            pass
    pick = st.query_params.get("pick")
    if pick is not None:
        st.session_state._pick_intent = pick
        try:
            del st.query_params["pick"]
        except Exception:
            pass
    fab = st.query_params.get("fab")
    if fab is not None:
        st.session_state._fab_intent = str(fab).strip().lower()
        try:
            del st.query_params["fab"]
        except Exception:
            pass


def apply_nav_intents() -> None:
    if st.session_state.pop("_wake_intent", None):
        st.session_state.agent_burst = True
    pick = st.session_state.pop("_pick_intent", None)
    if pick is not None:
        # Leave hub so pick is processed as chat, not re-shown as hub flash.
        st.session_state.agent_burst = True
        st.query_params["pick"] = str(pick)
    fab = st.session_state.pop("_fab_intent", None)
    if not fab:
        return
    st.session_state.agent_burst = True
    if fab == "chat":
        st.session_state.fab_panel = None
    elif fab == "plan":
        st.session_state.pending_plan = True
        st.session_state.fab_panel = None
    elif fab in {"tt", "mail", "task"}:
        st.session_state.fab_panel = fab
    else:
        st.session_state.fab_panel = None


def persist_user_data() -> None:
    uid = st.session_state.get("user_id")
    if not uid:
        return
    profile = st.session_state.profile
    messages = st.session_state.get("messages", [])
    save_session(uid, dumps_profile(profile), json.dumps(messages, ensure_ascii=False))


def default_welcome(lang: Lang) -> list[dict[str, str]]:
    return [{"role": "assistant", "content": t("welcome", lang)}]


def all_welcome_bodies() -> set[str]:
    return {t("welcome", code) for _, code in LANG_OPTIONS}


def chat_has_user_turn(messages: list[dict[str, str]]) -> bool:
    return any(m.get("role") == "user" for m in messages)


def sync_welcome_language(lang: Lang) -> None:
    """Update chat greeting when UI language changes."""
    msgs = st.session_state.get("messages")
    if not msgs:
        st.session_state.messages = default_welcome(lang)
        return
    welcomes = all_welcome_bodies()
    if msgs[0].get("role") == "assistant" and (
        msgs[0].get("content") in welcomes or len(msgs) == 1
    ):
        msgs[0]["content"] = t("welcome", lang)
        st.session_state.messages = msgs


def get_app_settings() -> AppSettings:
    if "app_settings" not in st.session_state:
        prof = st.session_state.get("profile")
        if prof and getattr(prof, "settings", None):
            st.session_state.app_settings = AppSettings.from_dict(prof.settings)
        else:
            st.session_state.app_settings = AppSettings()
    return st.session_state.app_settings  # type: ignore[return-value]


def save_app_settings(settings: AppSettings) -> None:
    st.session_state.app_settings = settings
    if "profile" in st.session_state:
        st.session_state.profile.settings = settings.to_dict()
    if st.session_state.get("user_id"):
        persist_user_data()


def load_user_data_once(lang: Lang) -> None:
    uid = st.session_state.get("user_id")
    if not uid or st.session_state.get("_db_loaded"):
        return
    data = load_session(uid)
    if data:
        prof_dict, _messages = data
        if prof_dict:
            st.session_state.profile = StudentProfile.from_dict(prof_dict)
        st.session_state.app_settings = AppSettings.from_dict(
            st.session_state.profile.settings
        )
    # Always land on bubble hub after login — do not restore stale chat from DB.
    reset_to_hub(lang, persist=True)
    st.session_state._db_loaded = True


def init_state(lang: Lang) -> None:
    if "profile" not in st.session_state:
        st.session_state.profile = StudentProfile()
    if "messages" not in st.session_state:
        st.session_state.messages = default_welcome(lang)
    elif st.session_state.get("_lang_init") != lang and not st.session_state.get("user_id"):
        st.session_state.messages = default_welcome(lang)
    st.session_state._lang_init = lang


def sidebar_settings(lang: Lang) -> Lang:
    settings = get_app_settings()
    with st.sidebar.expander("⚙️ " + t("settings_title", lang), expanded=False):
        labels = [label for label, _ in LANG_OPTIONS]
        codes: list[Lang] = [code for _, code in LANG_OPTIONS]  # type: ignore[misc]
        lang_idx = st.selectbox(
            t("lang_label", lang),
            range(len(labels)),
            format_func=lambda i: labels[i],
            index=codes.index(lang) if lang in codes else 0,
            key="settings_lang_idx",
        )
        font_idx = st.selectbox(
            t("settings_font", lang),
            range(3),
            format_func=lambda i: [t("font_small", lang), t("font_medium", lang), t("font_large", lang)][i],
            index=["small", "medium", "large"].index(settings.font_size),
            key="settings_font_idx",
        )
        theme_idx = st.radio(
            t("settings_theme", lang),
            [0, 1],
            format_func=lambda i: t("theme_light", lang) if i == 0 else t("theme_dark", lang),
            index=0 if settings.theme == "light" else 1,
            horizontal=True,
            key="settings_theme_idx",
        )
        pers_idx = st.selectbox(
            t("settings_personality", lang),
            range(3),
            format_func=lambda i: [
                t("personality_playful", lang),
                t("personality_balanced", lang),
                t("personality_calm", lang),
            ][i],
            index=["playful", "balanced", "calm"].index(settings.personality),
            key="settings_pers_idx",
        )

        if st.button(t("settings_apply", lang), use_container_width=True, key="settings_apply_btn"):
            new_lang = codes[lang_idx]
            new_settings = AppSettings(
                font_size=["small", "medium", "large"][font_idx],  # type: ignore[arg-type]
                theme="light" if theme_idx == 0 else "dark",
                personality=["playful", "balanced", "calm"][pers_idx],  # type: ignore[arg-type]
            )
            st.session_state.ui_lang = new_lang
            save_app_settings(new_settings)
            sync_welcome_language(new_lang)
            st.rerun()
    return get_lang()


def render_plugin_download(lang: Lang, *, key: str) -> None:
    st.caption(t("plugin_hint", lang))
    try:
        data = extension_zip_bytes()
        st.download_button(
            t("plugin_download", lang),
            data=data,
            file_name="bubu-fab-extension.zip",
            mime="application/zip",
            use_container_width=True,
            key=key,
        )
    except FileNotFoundError:
        st.warning("extension/ missing")


def login_screen(lang: Lang) -> None:
    render_login_header(t("login_title", lang), t("login_hint", lang))
    with st.expander(t("plugin_section", lang), expanded=False):
        render_plugin_download(lang, key="plugin_dl_login")
    tab_in, tab_up = st.tabs([t("tab_login", lang), t("tab_register", lang)])

    with tab_in:
        u = st.text_input(t("username", lang), key="login_user")
        p = st.text_input(t("password", lang), type="password", key="login_pass")
        if st.button(t("btn_login", lang), type="primary", use_container_width=True):
            uid, name = login_user(u, p)
            if uid is None:
                st.error(t("auth_invalid", lang))
            else:
                st.session_state.user_id = uid
                st.session_state.display_name = name
                st.session_state.account_username = u.strip().lower()
                st.session_state._db_loaded = False
                st.rerun()

    with tab_up:
        u2 = st.text_input(t("username", lang), key="reg_user")
        p2 = st.text_input(t("password", lang), type="password", key="reg_pass")
        dn = st.text_input(t("display_name", lang), key="reg_name")
        if st.button(t("btn_register", lang), use_container_width=True):
            ok, code = register_user(u2, p2, dn)
            if not ok:
                err = {
                    "username_too_short": t("auth_short_user", lang),
                    "password_too_short": t("auth_short_pass", lang),
                    "username_taken": t("auth_taken", lang),
                }.get(code, t("auth_invalid", lang))
                st.error(err)
            else:
                uid, name = login_user(u2, p2)
                st.session_state.user_id = uid
                st.session_state.display_name = name or dn or u2
                st.session_state.account_username = u2.strip().lower()
                st.session_state._db_loaded = False
                st.success(t("register_ok", lang))
                st.rerun()


def sidebar_profile(lang: Lang) -> None:
    p: StudentProfile = st.session_state.profile
    if st.session_state.get("user_id"):
        st.sidebar.success(
            t("logged_as", lang, name=st.session_state.get("display_name", ""))
        )
        st.sidebar.caption(f"{bot_nick(lang)} · {PROJECT_CREDIT}")
        st.sidebar.html(pulse_html(p, lang), width="stretch")
        with st.sidebar.expander(t("plugin_section", lang), expanded=False):
            render_plugin_download(lang, key="plugin_dl_sidebar")
        if st.sidebar.button(t("new_chat", lang), use_container_width=True):
            reset_to_hub(lang, persist=True)
            st.rerun()
        if st.sidebar.button(t("logout", lang), use_container_width=True):
            for key in (
                "user_id",
                "display_name",
                "account_username",
                "_db_loaded",
                "profile",
                "messages",
                "app_settings",
                "agent_burst",
                "_wake_intent",
                "_pick_intent",
                "_fab_intent",
                "fab_panel",
                "mail_draft",
                "_ui_revision",
            ):
                st.session_state.pop(key, None)
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.rerun()

    st.sidebar.header(t("sidebar_profile", lang))
    p.name = st.sidebar.text_input(t("name", lang), value=p.name)
    p.student_id = st.sidebar.text_input(t("student_id", lang), value=p.student_id)
    p.programme = st.sidebar.text_input(t("programme", lang), value=p.programme)
    if st.session_state.get("user_id") and st.sidebar.button(
        t("save_profile", lang), use_container_width=True, key="save_profile_btn"
    ):
        persist_user_data()
        st.sidebar.success(t("profile_saved", lang))

    st.sidebar.subheader(t("timetable", lang))
    st.sidebar.caption(t("tt_image_tip", lang))
    tt_img = st.sidebar.file_uploader(
        t("upload_tt_image", lang),
        type=["png", "jpg", "jpeg", "webp"],
        key="tt_image",
    )

    def _apply_timetable_slots(slots: list, *, file_sig: str | None = None) -> None:
        p.timetable = slots
        if file_sig:
            st.session_state._tt_scanned_sig = file_sig
        persist_user_data()
        st.sidebar.success(t("imported_slots", lang, n=len(slots)))
        # Tell the chat thread so history matches injected profile.
        note = t("tt_scan_ok_chat", lang, n=len(slots))
        msgs = list(st.session_state.get("messages") or [])
        welcomes = all_welcome_bodies()
        msgs = [
            m
            for m in msgs
            if not (m.get("role") == "assistant" and m.get("content") in welcomes)
        ]
        msgs.append({"role": "assistant", "content": note})
        st.session_state.messages = msgs
        st.session_state.agent_burst = True

    def _run_tt_scan(*, mark_sig: str | None = None) -> None:
        if not tt_img:
            st.sidebar.warning(t("upload_tt_image", lang))
            return
        with st.spinner(t("scanning_tt", lang)):
            try:
                mime = tt_img.type or "image/png"
                slots = parse_timetable_from_image(tt_img.getvalue(), mime=mime)
                if slots:
                    _apply_timetable_slots(slots, file_sig=mark_sig)
                    st.rerun()
                else:
                    # Mark attempted so auto-scan won't hammer the vision API every rerun.
                    if mark_sig:
                        st.session_state._tt_scanned_sig = mark_sig
                    st.sidebar.warning(t("vision_fail", lang))
            except Exception as exc:
                if mark_sig:
                    st.session_state._tt_scanned_sig = mark_sig
                st.sidebar.error(f"{t('vision_fail', lang)}\n{exc}")

    # Auto-scan once per newly uploaded file (chat box cannot see sidebar uploads).
    if tt_img is not None:
        file_sig = f"{tt_img.name}:{tt_img.size}:{getattr(tt_img, 'file_id', '')}"
        if st.session_state.get("_tt_scanned_sig") != file_sig:
            _run_tt_scan(mark_sig=file_sig)

    if st.sidebar.button(t("scan_tt", lang), use_container_width=True):
        mark = None
        if tt_img is not None:
            mark = f"{tt_img.name}:{tt_img.size}:{getattr(tt_img, 'file_id', '')}"
        _run_tt_scan(mark_sig=mark)

    if p.timetable:
        # Keep collapsed by default — pulse card already shows today; avoids sidebar overflow.
        with st.sidebar.expander("📅 " + t("timetable", lang), expanded=False):
            st.html(week_grid_html(p), width="stretch")
            st.markdown(analyze_timetable(p))
            st.caption(t("tt_ready_hint", lang))
            st.caption(t("tt_gaps_caption", lang))

    st.sidebar.subheader(t("tasks", lang))
    new_task = st.sidebar.text_input(t("new_task", lang))
    new_due = st.sidebar.text_input(t("new_due", lang))
    if st.sidebar.button(t("add_task", lang)):
        if new_task.strip():
            p.tasks.append(TaskItem(title=new_task.strip(), due=new_due.strip()))
            st.sidebar.success(t("task_added", lang))
            persist_user_data()

    if p.tasks:
        with st.sidebar.expander("✅ " + t("tasks", lang), expanded=False):
            for task in p.tasks[-12:]:
                st.caption(f"[{task.due or '—'}] {task.title}")

    st.sidebar.subheader(t("email_section", lang))
    st.sidebar.caption(t("email_hint", lang))
    mail_img = st.sidebar.file_uploader(
        t("upload_email_shot", lang),
        type=["png", "jpg", "jpeg", "webp"],
        key="mail_image_v2",
    )
    tone_map = {
        t("email_tone_polite", lang): "polite",
        t("email_tone_concise", lang): "concise",
        t("email_tone_friendly", lang): "friendly",
    }
    tone_choice = st.sidebar.selectbox(
        t("email_tone", lang),
        options=list(tone_map.keys()),
        key="mail_tone_v2",
    )
    add_mail_tasks = st.sidebar.checkbox(
        t("email_add_tasks", lang), value=True, key="mail_add_tasks_v2"
    )

    def _run_mail_draft(*, mark_sig: str | None = None) -> None:
        if not mail_img:
            st.sidebar.warning(t("upload_email_shot", lang))
            return
        with st.spinner(t("scanning_email", lang)):
            try:
                mime = mail_img.type or "image/png"
                result = draft_reply_from_email_image(
                    mail_img.getvalue(),
                    mime=mime,
                    tone=tone_map.get(tone_choice, "polite"),
                    lang=lang,
                )
                if mark_sig:
                    st.session_state._mail_scanned_sig = mark_sig
                st.session_state.mail_draft = result
                p.emails.insert(
                    0,
                    EmailSnippet(
                        subject=result.subject or "(screenshot)",
                        sender=result.sender,
                        date=result.date,
                        body_preview=(result.summary or result.reply_body)[:500],
                    ),
                )
                if add_mail_tasks:
                    for item in result.tasks:
                        p.tasks.append(
                            TaskItem(
                                title=item["title"],
                                due=item.get("due", ""),
                                source="email",
                            )
                        )
                note = format_draft_for_chat(result, lang)
                msgs = list(st.session_state.get("messages") or [])
                welcomes = all_welcome_bodies()
                msgs = [
                    m
                    for m in msgs
                    if not (m.get("role") == "assistant" and m.get("content") in welcomes)
                ]
                msgs.append({"role": "assistant", "content": note})
                st.session_state.messages = msgs
                st.session_state.agent_burst = True
                persist_user_data()
                st.sidebar.success(t("email_ok", lang))
                st.rerun()
            except Exception as exc:
                if mark_sig:
                    st.session_state._mail_scanned_sig = mark_sig
                st.sidebar.error(f"{t('email_vision_fail', lang)}\n{exc}")

    if st.sidebar.button(t("scan_email_reply", lang), use_container_width=True, key="scan_mail_btn"):
        mark = None
        if mail_img is not None:
            mark = f"{mail_img.name}:{mail_img.size}:{getattr(mail_img, 'file_id', '')}"
        _run_mail_draft(mark_sig=mark)

    draft = st.session_state.get("mail_draft")
    if draft is not None:
        with st.sidebar.expander(t("email_ok", lang), expanded=True):
            if draft.summary:
                st.caption(f"{t('email_summary_label', lang)}: {draft.summary}")
            if draft.reply_subject:
                st.text_input(
                    t("email_reply_subject", lang),
                    value=draft.reply_subject,
                    key="mail_reply_subject_view",
                )
            st.text_area(
                t("email_reply_body", lang),
                value=draft.reply_body,
                height=180,
                key="mail_reply_body_view",
            )

    with st.sidebar.expander(t("more_options", lang), expanded=False):
        p.custom_notes = st.sidebar.text_area(t("notes", lang), value=p.custom_notes, height=50)


def run_plan_week(lang: Lang, p: StudentProfile, settings: AppSettings) -> None:
    with st.spinner(t("planning", lang)):
        try:
            plan = suggest_study_plan(
                p,
                lang=lang,
                display_name=st.session_state.get("display_name", ""),
                account_username=st.session_state.get("account_username", ""),
                personality=settings.personality,
            )
            welcomes = all_welcome_bodies()
            st.session_state.messages = [
                m
                for m in st.session_state.messages
                if not (m.get("role") == "assistant" and m.get("content") in welcomes)
            ]
            st.session_state.messages.append({"role": "user", "content": t("plan_week", lang)})
            st.session_state.messages.append({"role": "assistant", "content": plan})
            st.session_state.agent_burst = True
            persist_user_data()
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))


def render_fab_feature_panel(lang: Lang) -> None:
    """Main-area panel opened from floating orb (tt / mail / task)."""
    panel = st.session_state.get("fab_panel")
    if panel not in {"tt", "mail", "task"}:
        return
    p: StudentProfile = st.session_state.profile
    titles = {
        "tt": t("fab_panel_tt", lang),
        "mail": t("fab_panel_mail", lang),
        "task": t("fab_panel_task", lang),
    }
    head_l, head_r = st.columns([4, 1])
    with head_l:
        st.subheader(titles[panel])
    with head_r:
        if st.button(t("fab_panel_close", lang), key="fab_panel_close_btn"):
            st.session_state.fab_panel = None
            st.rerun()

    if panel == "tt":
        st.caption(t("tt_image_tip", lang))
        fab_tt = st.file_uploader(
            t("upload_tt_image", lang),
            type=["png", "jpg", "jpeg", "webp"],
            key="fab_tt_image",
        )
        if st.button(t("scan_tt", lang), use_container_width=True, key="fab_scan_tt"):
            if not fab_tt:
                st.warning(t("upload_tt_image", lang))
            else:
                with st.spinner(t("scanning_tt", lang)):
                    try:
                        slots = parse_timetable_from_image(
                            fab_tt.getvalue(), mime=fab_tt.type or "image/png"
                        )
                        if slots:
                            p.timetable = slots
                            note = t("tt_scan_ok_chat", lang, n=len(slots))
                            msgs = list(st.session_state.get("messages") or [])
                            welcomes = all_welcome_bodies()
                            msgs = [
                                m
                                for m in msgs
                                if not (
                                    m.get("role") == "assistant"
                                    and m.get("content") in welcomes
                                )
                            ]
                            msgs.append({"role": "assistant", "content": note})
                            st.session_state.messages = msgs
                            st.session_state.agent_burst = True
                            st.session_state.fab_panel = None
                            persist_user_data()
                            st.success(t("imported_slots", lang, n=len(slots)))
                            st.rerun()
                        else:
                            st.warning(t("vision_fail", lang))
                    except Exception as exc:
                        st.error(f"{t('vision_fail', lang)}\n{exc}")
        return

    if panel == "mail":
        st.caption(t("email_hint", lang))
        fab_mail = st.file_uploader(
            t("upload_email_shot", lang),
            type=["png", "jpg", "jpeg", "webp"],
            key="fab_mail_image_v2",
        )
        tone_map = {
            t("email_tone_polite", lang): "polite",
            t("email_tone_concise", lang): "concise",
            t("email_tone_friendly", lang): "friendly",
        }
        tone_choice = st.selectbox(
            t("email_tone", lang),
            options=list(tone_map.keys()),
            key="fab_mail_tone_v2",
        )
        add_tasks = st.checkbox(t("email_add_tasks", lang), value=True, key="fab_mail_add_tasks_v2")
        if st.button(t("scan_email_reply", lang), use_container_width=True, key="fab_scan_mail"):
            if not fab_mail:
                st.warning(t("upload_email_shot", lang))
            else:
                with st.spinner(t("scanning_email", lang)):
                    try:
                        result = draft_reply_from_email_image(
                            fab_mail.getvalue(),
                            mime=fab_mail.type or "image/png",
                            tone=tone_map.get(tone_choice, "polite"),
                            lang=lang,
                        )
                        st.session_state.mail_draft = result
                        p.emails.insert(
                            0,
                            EmailSnippet(
                                subject=result.subject or "(screenshot)",
                                sender=result.sender,
                                date=result.date,
                                body_preview=(result.summary or result.reply_body)[:500],
                            ),
                        )
                        if add_tasks:
                            for item in result.tasks:
                                p.tasks.append(
                                    TaskItem(
                                        title=item["title"],
                                        due=item.get("due", ""),
                                        source="email",
                                    )
                                )
                        note = format_draft_for_chat(result, lang)
                        msgs = list(st.session_state.get("messages") or [])
                        welcomes = all_welcome_bodies()
                        msgs = [
                            m
                            for m in msgs
                            if not (
                                m.get("role") == "assistant" and m.get("content") in welcomes
                            )
                        ]
                        msgs.append({"role": "assistant", "content": note})
                        st.session_state.messages = msgs
                        st.session_state.agent_burst = True
                        st.session_state.fab_panel = None
                        persist_user_data()
                        st.success(t("email_ok", lang))
                        st.rerun()
                    except Exception as exc:
                        st.error(f"{t('email_vision_fail', lang)}\n{exc}")
        draft = st.session_state.get("mail_draft")
        if draft is not None:
            if draft.reply_subject:
                st.text_input(
                    t("email_reply_subject", lang),
                    value=draft.reply_subject,
                    key="fab_mail_subj_view",
                )
            st.text_area(
                t("email_reply_body", lang),
                value=draft.reply_body,
                height=160,
                key="fab_mail_body_view",
            )
        return

    # task
    new_task = st.text_input(t("new_task", lang), key="fab_new_task")
    new_due = st.text_input(t("new_due", lang), key="fab_new_due")
    if st.button(t("add_task", lang), use_container_width=True, key="fab_add_task"):
        if new_task.strip():
            p.tasks.append(TaskItem(title=new_task.strip(), due=new_due.strip()))
            persist_user_data()
            st.success(t("task_added", lang))
            st.session_state.fab_panel = None
            st.rerun()
        else:
            st.warning(t("new_task", lang))


def consume_bubble_pick_query(prompts: list[str], *, plan_index: int | None) -> None:
    pick = st.query_params.get("pick")
    if pick is None:
        return
    try:
        idx = int(pick)
    except ValueError:
        try:
            del st.query_params["pick"]
        except Exception:
            pass
        return
    try:
        del st.query_params["pick"]
    except Exception:
        pass
    if plan_index is not None and idx == plan_index:
        st.session_state.pending_plan = True
    elif 0 <= idx < len(prompts):
        st.session_state.pending_prompt = prompts[idx]


def main_chat(lang: Lang) -> None:
    p: StudentProfile = st.session_state.profile
    settings = get_app_settings()
    messages = st.session_state.messages
    pristine = not chat_has_user_turn(messages)
    agent_burst = st.session_state.get("agent_burst", False)
    show_agent_hub = pristine and not agent_burst
    prompts = [t("q1", lang), t("q2", lang), t("q3", lang), t("q4", lang)]
    plan_index = len(prompts)
    auth_token = ensure_auth_query_param()

    consume_bubble_pick_query(prompts, plan_index=plan_index)

    if st.session_state.pop("pending_plan", None):
        run_plan_week(lang, p, settings)
        return

    # Deep-link panel from browser extension (?fab=tt|mail|task)
    if st.session_state.get("fab_panel") in {"tt", "mail", "task"}:
        inject_ui_phase("chat")
        render_fab_feature_panel(lang)
        return

    # Recompute after pick may have set pending and after wake intent applied
    pristine = not chat_has_user_turn(st.session_state.messages)
    agent_burst = st.session_state.get("agent_burst", False)
    show_agent_hub = pristine and not agent_burst

    if show_agent_hub:
        inject_ui_phase("hub")
        render_agent_bubble(
            t("agent_bubble_hint", lang),
            on_wake=None,
            auth_token=auth_token,
            brand=t("hub_brand", lang),
            title_line1=t("hub_title_1", lang),
            title_line2=t("hub_title_2", lang),
            cta=t("hub_cta", lang),
            credit=t("hub_credit", lang),
        )
        with st.expander(t("plugin_section", lang), expanded=False):
            render_plugin_download(lang, key="plugin_dl_hub")
    elif pristine and agent_burst:
        inject_ui_phase("burst")
        render_mini_prompt_bubbles(
            prompts,
            plan_label=t("plan_week", lang),
            hint=t("burst_pick_hint", lang),
            auth_token=auth_token,
        )
    else:
        inject_ui_phase("chat")
        render_chat_thread(messages)

    pending = st.session_state.pop("pending_prompt", None)
    chat_ready = not show_agent_hub
    user_input = st.chat_input(t("chat_placeholder", lang)) if chat_ready else None
    if pending:
        user_input = pending

    if user_input:
        st.session_state.agent_burst = True
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] in ("user", "assistant")
        ]
        st.session_state.messages.append({"role": "user", "content": user_input})
        if not (pristine and agent_burst):
            render_chat_thread(st.session_state.messages[:-1])
        st.markdown(
            f'<div class="chat-line user"><span class="chat-pill">{html.escape(user_input)}</span></div>',
            unsafe_allow_html=True,
        )
        body = begin_ai_stream()
        with body:
            try:
                stream = chat_completion_stream(
                    user_input,
                    history,
                    p,
                    lang=lang,
                    display_name=st.session_state.get("display_name", ""),
                    account_username=st.session_state.get("account_username", ""),
                    personality=settings.personality,
                )
                reply = st.write_stream(stream)
            except RuntimeError as e:
                reply = str(e)
                st.error(reply)
            except Exception as e:
                reply = str(e)
                st.error(reply)
        welcomes = all_welcome_bodies()
        st.session_state.messages = [
            m
            for m in st.session_state.messages
            if not (m.get("role") == "assistant" and m.get("content") in welcomes)
        ]
        st.session_state.messages.append({"role": "assistant", "content": reply})
        persist_user_data()
        st.rerun()


def main() -> None:
    load_server_secrets()
    init_db()
    lang = get_lang()

    # Bubble <a href> causes full reload → new session. Restore user, then nav intents.
    restore_auth_from_query()
    capture_nav_intents()

    if not st.session_state.get("user_id"):
        inject_bu_theme(get_app_settings())
        lang = sidebar_settings(lang)
        login_screen(lang)
        return

    init_state(lang)
    if st.session_state.get("user_id") and st.session_state.get("_ui_revision") != _UI_REVISION:
        st.session_state._ui_revision = _UI_REVISION
        st.session_state._db_loaded = False
    load_user_data_once(lang)
    apply_nav_intents()
    if "messages" not in st.session_state:
        st.session_state.messages = default_welcome(lang)
    if "app_settings" not in st.session_state and "profile" in st.session_state:
        st.session_state.app_settings = AppSettings.from_dict(st.session_state.profile.settings)

    ensure_auth_query_param()
    inject_bu_theme(get_app_settings())
    lang = sidebar_settings(lang)
    sidebar_profile(lang)
    main_chat(lang)


if __name__ == "__main__":
    main()

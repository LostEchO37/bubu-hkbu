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
            "HKBU_SESSION_SECRET",
        ):
            if key in st.secrets:
                os.environ[key] = str(st.secrets[key])
    except Exception:
        pass
    if not os.environ.get("LLM_PROVIDER"):
        os.environ["LLM_PROVIDER"] = "hkbu"

from core.agent import chat_completion_stream, suggest_study_plan

try:
    from core.agent import get_last_retrieval
except ImportError:  # pragma: no cover — Cloud partial deploys
    def get_last_retrieval():  # type: ignore[misc]
        return None


try:
    from core.live_facts import AR_CALENDAR, HKO_HOME, fetch_weather, official_links
except ImportError:  # pragma: no cover
    AR_CALENDAR = "https://calendar.ar.hkbu.edu.hk/"
    HKO_HOME = "https://www.hko.gov.hk/"

    def fetch_weather(lang="zh-CN", *, force=False):  # type: ignore[misc]
        class _W:
            ok = False

            def one_line(self, _lang=None):
                return ""

        return _W()

    def official_links(lang="zh-CN"):  # type: ignore[misc]
        return []
from core.app_settings import AppSettings
from core.auth import get_user_by_id, load_session, login_user, register_user, save_session
from core.session_token import make_auth_token, verify_auth_token
from core.database import init_db
from core.i18n import LANG_OPTIONS, Lang, parse_lang, t
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
    render_chat_thread,
    render_mini_prompt_bubbles,
)
from core.changelog import changelog_markdown
from core.identity import PROJECT_CREDIT, bot_nick
from core.today import pulse_html
from core.ui import (
    inject_bu_theme,
    inject_chunk_recovery,
    inject_ui_phase,
    render_login_header,
    safe_st_html,
)

# Bump when chat UI flow changes — forces one-time hub reset for logged-in sessions.
_UI_REVISION = 58

_FAVICON = Path(__file__).resolve().parent / "assets" / "bu_favicon.png"
st.set_page_config(
    page_title="阿Bu · HKBU Student Assistant",
    page_icon=str(_FAVICON) if _FAVICON.is_file() else "🫧",
    layout="wide",
    # Desktop skeleton: fixed left nav (UI-01). Narrow screens still use Streamlit drawer.
    initial_sidebar_state="expanded",
)

_NAV_PAGES = ("chat", "workspace", "tasks")


def ensure_nav_page() -> str:
    page = st.session_state.get("nav_page", "chat")
    if page not in _NAV_PAGES:
        page = "chat"
        st.session_state.nav_page = page
    return page


def set_nav_page(page: str) -> None:
    if page in _NAV_PAGES:
        st.session_state.nav_page = page


def plain_account_label(name: str) -> str:
    """Avoid mailto auto-link on emails (UI-12)."""
    raw = (name or "").strip() or "—"
    return raw.replace("@", "@\u200b")


def scroll_latest_assistant_into_view() -> None:
    """UI-07: after a reply, bring the latest message into the upper viewport."""
    script = """
<script>
(function () {
  function go() {
    try {
      var root = window.parent && window.parent.document ? window.parent.document : document;
      var msgs = root.querySelectorAll('[data-testid="stChatMessage"], .chat-line');
      if (!msgs || !msgs.length) return;
      var el = msgs[msgs.length - 1];
      el.scrollIntoView({ block: "center", behavior: "smooth" });
    } catch (e) {}
  }
  setTimeout(go, 120);
  setTimeout(go, 480);
})();
</script>
"""
    try:
        safe_st_html(script, width="content")
    except Exception:
        pass


def friendly_vision_error(lang: Lang, *, kind: str = "tt") -> str:
    """User-facing vision failure — never surface env/model names (UI-12)."""
    return t("email_vision_fail" if kind == "mail" else "vision_fail", lang)


def get_lang() -> Lang:
    if "ui_lang" not in st.session_state:
        st.session_state.ui_lang = "zh-CN"
    return parse_lang(st.session_state.ui_lang)


def restore_lang_from_query() -> None:
    """Bubble <a href> full-reloads wipe session — restore language from ?lang=."""
    q = st.query_params.get("lang")
    if q is None:
        return
    st.session_state.ui_lang = parse_lang(q)
    st.session_state._lang_user_set = True


def _qp_one(value: object) -> str | None:
    """Streamlit may return str or list for a query param."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return str(value[0]) if value else None
    return str(value)


def ensure_lang_query_param(lang: Lang) -> None:
    """Keep lang= in the URL so hub/burst HTML links preserve UI + chatbot language."""
    try:
        existing = _qp_one(st.query_params.get("lang"))
        if existing == lang:
            return
        st.query_params["lang"] = lang
    except Exception:
        pass


def set_ui_lang(lang: Lang, *, persist: bool = True) -> None:
    lang = parse_lang(lang)
    st.session_state.ui_lang = lang
    st.session_state._lang_user_set = True
    ensure_lang_query_param(lang)
    settings = get_app_settings()
    if settings.ui_lang != lang:
        settings.ui_lang = lang  # type: ignore[assignment]
        if persist:
            save_app_settings(settings)
        else:
            st.session_state.app_settings = settings
            if "profile" in st.session_state:
                st.session_state.profile.settings = settings.to_dict()
    sync_welcome_language(lang)


def on_streamlit_cloud() -> bool:
    """Community Cloud mounts the repo under /mount/src."""
    return Path("/mount/src").is_dir() or bool(
        os.environ.get("STREAMLIT_SHARING_MODE")
        or os.environ.get("STREAMLIT_RUNTIME_ENVIRONMENT")
    )


def reset_to_hub(lang: Lang, *, persist: bool = True, clear_burst: bool = True) -> None:
    """Welcome-only chat + bubble hub (clears stuck history)."""
    st.session_state.messages = default_welcome(lang)
    if clear_burst:
        st.session_state.agent_burst = False
    # Drop one-shot navigation flags only. Avoid rewriting auth/lang when unchanged —
    # query_param writes force frontend URL sync and can strand the loading spinner.
    try:
        for key in ("wake", "pick", "fab", "_bubu_r"):
            if key in st.query_params:
                del st.query_params[key]
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
    existing = _qp_one(st.query_params.get("auth"))
    # Reuse valid token — minting a new one every run would change the URL and loop-rerun.
    if existing and verify_auth_token(existing) == uid_i:
        return existing
    token = make_auth_token(uid_i)
    try:
        if existing != token:
            st.query_params["auth"] = token
    except Exception:
        pass
    return token


def capture_nav_intents() -> None:
    """Read wake/pick/fab before hub reset can interfere; apply after session hydrate."""
    wake = _qp_one(st.query_params.get("wake"))
    if wake == "1":
        st.session_state._wake_intent = True
        try:
            del st.query_params["wake"]
        except Exception:
            pass
    pick = _qp_one(st.query_params.get("pick"))
    if pick is not None:
        st.session_state._pick_intent = pick
        try:
            del st.query_params["pick"]
        except Exception:
            pass
    fab = _qp_one(st.query_params.get("fab"))
    if fab is not None:
        st.session_state._fab_intent = fab.strip().lower()
        try:
            del st.query_params["fab"]
        except Exception:
            pass


def apply_nav_intents() -> None:
    if st.session_state.pop("_wake_intent", None):
        st.session_state.agent_burst = True
    pick = st.session_state.pop("_pick_intent", None)
    if pick is not None:
        # Keep pick in session only — writing it back to the URL caused an endless rerun loop.
        st.session_state.agent_burst = True
        st.session_state._pending_pick = pick
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
    # Keep preferences chosen on the login screen (theme/font/tone/lang) over stale DB defaults.
    pre_login = st.session_state.get("app_settings")
    settings_chose = bool(st.session_state.get("_settings_user_set"))
    user_chose_lang = bool(st.session_state.get("_lang_user_set") or st.query_params.get("lang"))
    session_lang = parse_lang(st.session_state.get("ui_lang"), lang)
    data = load_session(uid)
    if data:
        prof_dict, _messages = data
        if prof_dict:
            st.session_state.profile = StudentProfile.from_dict(prof_dict)
        loaded = AppSettings.from_dict(st.session_state.profile.settings)
        if settings_chose and isinstance(pre_login, AppSettings):
            loaded = AppSettings(
                font_size=pre_login.font_size,
                theme=pre_login.theme,
                personality=pre_login.personality,
                ui_lang=pre_login.ui_lang,
            )
        st.session_state.app_settings = loaded
        st.session_state.profile.settings = loaded.to_dict()
        saved = parse_lang(loaded.ui_lang)
        if user_chose_lang or settings_chose:
            lang = session_lang if user_chose_lang else parse_lang(loaded.ui_lang)
            if st.session_state.app_settings.ui_lang != lang:
                st.session_state.app_settings.ui_lang = lang  # type: ignore[assignment]
                st.session_state.profile.settings = st.session_state.app_settings.to_dict()
        else:
            lang = saved
            st.session_state.ui_lang = lang
    else:
        if settings_chose and isinstance(pre_login, AppSettings):
            st.session_state.app_settings = pre_login
            if "profile" in st.session_state:
                st.session_state.profile.settings = pre_login.to_dict()
        lang = session_lang
        st.session_state.ui_lang = lang
    ensure_lang_query_param(lang)
    # Sync notes widget from loaded profile (avoid stale textarea key).
    st.session_state.custom_notes_area = getattr(
        st.session_state.get("profile"), "custom_notes", ""
    ) or ""
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


def _purge_stale_settings_keys(lang: Lang) -> None:
    """Drop legacy + other-language draft keys *before* widgets are created."""
    for legacy in (
        "settings_theme_idx",
        "settings_lang_idx",
        "settings_font_idx",
        "settings_pers_idx",
        "settings_font",
        "settings_theme",
        "settings_pers",
    ):
        st.session_state.pop(legacy, None)
    suffix = f"_{lang}"
    for key in list(st.session_state.keys()):
        if key.startswith("_set_font_") or key.startswith("_set_theme_") or key.startswith(
            "_set_pers_"
        ):
            if not str(key).endswith(suffix):
                st.session_state.pop(key, None)


def _settings_widget_state(lang: Lang) -> tuple[list[Lang], dict[str, str], list[str], list[str], str, str, list[str], list[str], str]:
    """Prepare settings widget keys for the current language."""
    settings = get_app_settings()
    _purge_stale_settings_keys(lang)
    codes: list[Lang] = [code for _, code in LANG_OPTIONS]  # type: ignore[misc]
    lang_labels = {code: label for label, code in LANG_OPTIONS}
    if st.session_state.get("settings_lang") not in codes:
        st.session_state.settings_lang = lang

    font_codes = ["small", "medium", "large"]
    font_labels = [t("font_small", lang), t("font_medium", lang), t("font_large", lang)]
    font_key = f"_set_font_{lang}"
    if st.session_state.get(font_key) not in font_labels:
        cur = settings.font_size if settings.font_size in font_codes else "medium"
        st.session_state[font_key] = font_labels[font_codes.index(cur)]

    theme_key = f"_set_theme_{lang}"
    if st.session_state.get(theme_key) not in ("light", "dark"):
        st.session_state[theme_key] = (
            settings.theme if settings.theme in ("light", "dark") else "light"
        )

    pers_codes = ["playful", "balanced", "calm"]
    pers_labels = [
        t("personality_playful", lang),
        t("personality_balanced", lang),
        t("personality_calm", lang),
    ]
    pers_key = f"_set_pers_{lang}"
    if st.session_state.get(pers_key) not in pers_labels:
        cur_p = settings.personality if settings.personality in pers_codes else "playful"
        st.session_state[pers_key] = pers_labels[pers_codes.index(cur_p)]
    return (
        codes,
        lang_labels,
        font_codes,
        font_labels,
        font_key,
        theme_key,
        pers_codes,
        pers_labels,
        pers_key,
    )


def _apply_settings_from_widgets(
    lang: Lang,
    *,
    chosen_lang: Lang,
    font_label: str,
    theme_choice: str,
    pers_label: str,
    font_codes: list[str],
    font_labels: list[str],
    pers_codes: list[str],
    pers_labels: list[str],
    lang_labels: dict[str, str],
) -> None:
    safe_theme = theme_choice if theme_choice in ("light", "dark") else "light"
    try:
        safe_font = font_codes[font_labels.index(font_label)]
    except ValueError:
        safe_font = "medium"
    try:
        safe_pers = pers_codes[pers_labels.index(pers_label)]
    except ValueError:
        safe_pers = "playful"
    new_lang = chosen_lang if chosen_lang in lang_labels or chosen_lang in ("zh-CN", "zh-TW", "en") else lang
    new_settings = AppSettings(
        font_size=safe_font,  # type: ignore[arg-type]
        theme=safe_theme,  # type: ignore[arg-type]
        personality=safe_pers,  # type: ignore[arg-type]
        ui_lang=new_lang,
    )
    st.session_state._lang_user_set = True
    st.session_state._settings_user_set = True
    st.session_state.ui_lang = new_lang
    ensure_lang_query_param(new_lang)
    save_app_settings(new_settings)
    sync_welcome_language(new_lang)
    tone_name = {
        "playful": t("personality_playful", new_lang),
        "balanced": t("personality_balanced", new_lang),
        "calm": t("personality_calm", new_lang),
    }[safe_pers]
    theme_name = t("theme_light", new_lang) if safe_theme == "light" else t("theme_dark", new_lang)
    st.session_state._settings_flash = t(
        "settings_applied",
        new_lang,
        lang_label=lang_labels.get(new_lang, new_lang),
        tone=tone_name,
        theme=theme_name,
    )


def render_settings_form(lang: Lang, *, key_prefix: str = "dlg") -> Lang:
    """Settings body used in dialogs (UI-03 / UI-13)."""
    (
        codes,
        lang_labels,
        font_codes,
        font_labels,
        font_key,
        theme_key,
        pers_codes,
        pers_labels,
        pers_key,
    ) = _settings_widget_state(lang)
    settings = get_app_settings()
    active_tone = {
        "playful": t("personality_playful", lang),
        "balanced": t("personality_balanced", lang),
        "calm": t("personality_calm", lang),
    }.get(settings.personality, t("personality_playful", lang))
    st.caption(t("tone_active", lang, tone=active_tone))
    chosen_lang = st.selectbox(
        t("lang_label", lang),
        codes,
        format_func=lambda c: lang_labels.get(c, c),
        key=f"{key_prefix}_settings_lang",
    )
    # Keep legacy key in sync for apply path
    st.session_state.settings_lang = chosen_lang
    font_label = st.selectbox(
        t("settings_font", lang),
        font_labels,
        key=f"{key_prefix}_{font_key}",
    )
    st.session_state[font_key] = font_label
    theme_choice = st.radio(
        t("settings_theme", lang),
        ["light", "dark"],
        format_func=lambda v: t("theme_light", lang) if v == "light" else t("theme_dark", lang),
        horizontal=True,
        key=f"{key_prefix}_{theme_key}",
    )
    st.session_state[theme_key] = theme_choice
    pers_label = st.selectbox(
        t("settings_personality", lang),
        pers_labels,
        key=f"{key_prefix}_{pers_key}",
    )
    st.session_state[pers_key] = pers_label
    if st.button(t("settings_apply", lang), type="primary", use_container_width=True, key=f"{key_prefix}_apply"):
        _apply_settings_from_widgets(
            lang,
            chosen_lang=chosen_lang,  # type: ignore[arg-type]
            font_label=font_label,
            theme_choice=theme_choice,
            pers_label=pers_label,
            font_codes=font_codes,
            font_labels=font_labels,
            pers_codes=pers_codes,
            pers_labels=pers_labels,
            lang_labels=lang_labels,
        )
        st.rerun()

    st.markdown("---")
    st.caption(t("help_section", lang))
    with st.expander(t("help_tips_title", lang), expanded=False):
        st.caption(t("sharing_public_tip", lang))
        st.caption(t("cold_start_tip", lang))
        st.caption(t("chunk_reload_tip", lang))
    if on_streamlit_cloud():
        st.caption(t("storage_cloud_note", lang))
    st.caption(t("plugin_section", lang))
    render_plugin_download(lang, key=f"{key_prefix}_plugin")
    ensure_lang_query_param(get_lang())
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


@st.dialog("📋 更新日志 / Changelog")
def _changelog_dialog(lang: Lang) -> None:
    st.caption(t("changelog_privacy", lang))
    st.markdown(changelog_markdown(lang))


@st.dialog("⚙️ Settings")
def _settings_dialog(lang: Lang) -> None:
    render_settings_form(lang, key_prefix="setdlg")


def do_logout(lang: Lang) -> None:
    keep_lang = parse_lang(st.session_state.get("ui_lang"), lang)
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
        "settings_theme_idx",
        "settings_lang_idx",
        "settings_font_idx",
        "settings_pers_idx",
        "settings_theme",
        "settings_lang",
        "settings_font",
        "settings_pers",
        "custom_notes_area",
        "_settings_flash",
        "settings_panel_open",
        "_settings_user_set",
        "nav_page",
        "ws_seg",
        "_scroll_chat",
    ):
        st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        if str(key).startswith("_set_font_") or str(key).startswith("_set_theme_") or str(
            key
        ).startswith("_set_pers_"):
            st.session_state.pop(key, None)
    try:
        st.query_params.clear()
        st.query_params["lang"] = keep_lang
    except Exception:
        pass
    st.session_state.ui_lang = keep_lang
    st.session_state._lang_user_set = True
    st.rerun()


def login_screen(lang: Lang) -> None:
    """UI-08: single centered card — title, hint, auth, soft storage note, text links."""
    st.markdown('<div class="bu-login-shell" aria-hidden="true"></div>', unsafe_allow_html=True)
    render_login_header(t("login_title", lang), t("login_hint", lang))
    mode = st.radio(
        t("login_title", lang),
        [t("tab_login", lang), t("tab_register", lang)],
        horizontal=True,
        label_visibility="collapsed",
        key="login_mode",
    )
    if mode == t("tab_login", lang):
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
                st.session_state.nav_page = "chat"
                st.rerun()
    else:
        u2 = st.text_input(t("username", lang), key="reg_user")
        p2 = st.text_input(t("password", lang), type="password", key="reg_pass")
        dn = st.text_input(t("display_name", lang), key="reg_name")
        if st.button(t("btn_register", lang), type="primary", use_container_width=True):
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
                st.session_state.nav_page = "chat"
                st.success(t("register_ok", lang))
                st.rerun()
    if on_streamlit_cloud():
        st.caption(t("storage_cloud_note", lang))
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button(t("changelog_title", lang), use_container_width=True, key="login_changelog"):
            _changelog_dialog(lang)
    with b2:
        if st.button(t("nav_settings", lang), use_container_width=True, key="login_settings"):
            _settings_dialog(lang)
    with b3:
        if st.button(t("help_section", lang), use_container_width=True, key="login_help"):
            _settings_dialog(lang)


def render_app_sidebar(lang: Lang) -> Lang:
    """UI-03: brand → nav → today pulse → account / logout / settings."""
    flash = st.session_state.pop("_settings_flash", None)
    if flash:
        st.sidebar.caption(flash)

    st.sidebar.markdown(
        f'<div class="bu-nav-brand">{html.escape(bot_nick(lang))}</div>',
        unsafe_allow_html=True,
    )

    ensure_nav_page()
    page_ids = list(_NAV_PAGES)
    page_labels = [t("nav_chat", lang), t("nav_workspace", lang), t("nav_tasks", lang)]
    current = st.session_state.get("nav_page", "chat")
    try:
        idx = page_ids.index(current)
    except ValueError:
        idx = 0
    choice = st.sidebar.radio(
        "nav",
        page_labels,
        index=idx,
        label_visibility="collapsed",
        key="nav_page_radio",
    )
    st.session_state.nav_page = page_ids[page_labels.index(choice)]

    if st.session_state.get("user_id") and "profile" in st.session_state:
        st.sidebar.markdown(
            pulse_html(st.session_state.profile, lang),
            unsafe_allow_html=True,
        )

    account = st.session_state.get("account_username") or st.session_state.get("display_name") or ""
    st.sidebar.markdown(
        f'<div class="bu-account-plain">{html.escape(t("logged_as", lang, name=plain_account_label(str(account))))}</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button(t("new_chat", lang), use_container_width=True, key="btn_new_chat"):
            reset_to_hub(lang, persist=True)
            set_nav_page("chat")
            st.rerun()
    with c2:
        if st.button(t("logout", lang), use_container_width=True, key="btn_logout"):
            do_logout(lang)
    if st.sidebar.button(t("nav_settings", lang), use_container_width=True, key="btn_open_settings"):
        _settings_dialog(lang)
    st.sidebar.markdown(
        f'<div class="bu-nav-credit">{html.escape(PROJECT_CREDIT)}</div>',
        unsafe_allow_html=True,
    )
    ensure_lang_query_param(get_lang())
    return get_lang()


def _append_assistant_note(note: str) -> None:
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
    set_nav_page("chat")
    st.session_state._scroll_chat = True


def render_workspace_panel(lang: Lang) -> None:
    """UI-06: workspace page with one segment at a time (no chat in the middle)."""
    p: StudentProfile = st.session_state.profile
    st.markdown(
        f'<div class="bu-workspace-head"><h3>{html.escape(t("workspace_title", lang))}</h3>'
        f'<p>{html.escape(t("workspace_hint", lang))}</p></div>',
        unsafe_allow_html=True,
    )
    seg_ids = ["profile", "timetable", "mail", "notes"]
    seg_labels = [
        t("ws_seg_profile", lang),
        t("ws_seg_timetable", lang),
        t("ws_seg_mail", lang),
        t("ws_seg_notes", lang),
    ]
    if st.session_state.get("ws_seg") not in seg_labels:
        st.session_state.ws_seg = seg_labels[0]
    seg = st.radio(
        "ws_seg",
        seg_labels,
        horizontal=True,
        label_visibility="collapsed",
        key="ws_seg",
    )
    seg_id = seg_ids[seg_labels.index(seg)]

    if seg_id == "profile":
        p.name = st.text_input(t("name", lang), value=p.name, key="ws_name")
        p.student_id = st.text_input(t("student_id", lang), value=p.student_id, key="ws_sid")
        p.programme = st.text_input(t("programme", lang), value=p.programme, key="ws_prog")
        if st.session_state.get("user_id") and st.button(
            t("save_profile", lang), type="primary", use_container_width=True, key="save_profile_btn"
        ):
            persist_user_data()
            st.success(t("profile_saved", lang))
        return

    if seg_id == "timetable":
        st.caption(t("tt_image_tip", lang))
        st.markdown(
            f'<div class="bu-upload-box"><p>{html.escape(t("upload_box_hint", lang))}</p></div>',
            unsafe_allow_html=True,
        )
        tt_img = st.file_uploader(
            t("upload_tt_image", lang),
            type=["png", "jpg", "jpeg", "webp"],
            key="tt_image",
        )

        def _apply_timetable_slots(slots: list, *, file_sig: str | None = None) -> None:
            p.timetable = slots
            if file_sig:
                st.session_state._tt_scanned_sig = file_sig
            persist_user_data()
            st.success(t("imported_slots", lang, n=len(slots)))
            _append_assistant_note(t("tt_scan_ok_chat", lang, n=len(slots)))

        def _run_tt_scan(*, mark_sig: str | None = None) -> None:
            if not tt_img:
                st.warning(t("upload_tt_image", lang))
                return
            with st.spinner(t("scanning_tt", lang)):
                try:
                    mime = tt_img.type or "image/png"
                    slots = parse_timetable_from_image(tt_img.getvalue(), mime=mime)
                    if slots:
                        _apply_timetable_slots(slots, file_sig=mark_sig)
                        st.rerun()
                    else:
                        if mark_sig:
                            st.session_state._tt_scanned_sig = mark_sig
                        st.warning(friendly_vision_error(lang, kind="tt"))
                except Exception:
                    if mark_sig:
                        st.session_state._tt_scanned_sig = mark_sig
                    st.error(friendly_vision_error(lang, kind="tt"))

        if tt_img is not None:
            file_sig = f"{tt_img.name}:{tt_img.size}:{getattr(tt_img, 'file_id', '')}"
            if st.session_state.get("_tt_scanned_sig") != file_sig:
                _run_tt_scan(mark_sig=file_sig)

        if st.button(t("scan_tt", lang), type="primary", use_container_width=True, key="ws_scan_tt"):
            mark = None
            if tt_img is not None:
                mark = f"{tt_img.name}:{tt_img.size}:{getattr(tt_img, 'file_id', '')}"
            _run_tt_scan(mark_sig=mark)

        if p.timetable:
            st.markdown(week_grid_html(p), unsafe_allow_html=True)
            st.markdown(analyze_timetable(p))
            st.caption(t("tt_ready_hint", lang))
            st.caption(t("tt_gaps_caption", lang))
        return

    if seg_id == "mail":
        st.caption(t("email_hint", lang))
        st.markdown(
            f'<div class="bu-upload-box"><p>{html.escape(t("upload_box_hint", lang))}</p></div>',
            unsafe_allow_html=True,
        )
        mail_img = st.file_uploader(
            t("upload_email_shot", lang),
            type=["png", "jpg", "jpeg", "webp"],
            key="mail_image_v2",
        )
        tone_map = {
            t("email_tone_polite", lang): "polite",
            t("email_tone_concise", lang): "concise",
            t("email_tone_friendly", lang): "friendly",
        }
        tone_choice = st.selectbox(
            t("email_tone", lang),
            options=list(tone_map.keys()),
            key="mail_tone_v2",
        )
        add_mail_tasks = st.checkbox(
            t("email_add_tasks", lang), value=True, key="mail_add_tasks_v2"
        )

        def _run_mail_draft(*, mark_sig: str | None = None) -> None:
            if not mail_img:
                st.warning(t("upload_email_shot", lang))
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
                    _append_assistant_note(format_draft_for_chat(result, lang))
                    persist_user_data()
                    st.success(t("email_ok", lang))
                    st.rerun()
                except Exception:
                    if mark_sig:
                        st.session_state._mail_scanned_sig = mark_sig
                    st.error(friendly_vision_error(lang, kind="mail"))

        if st.button(
            t("scan_email_reply", lang), type="primary", use_container_width=True, key="scan_mail_btn"
        ):
            mark = None
            if mail_img is not None:
                mark = f"{mail_img.name}:{mail_img.size}:{getattr(mail_img, 'file_id', '')}"
            _run_mail_draft(mark_sig=mark)

        draft = st.session_state.get("mail_draft")
        if draft is not None:
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
                height=140,
                key="mail_reply_body_view",
            )
        return

    # notes
    st.caption(t("notes_hint", lang))
    if "custom_notes_area" not in st.session_state:
        st.session_state.custom_notes_area = p.custom_notes or ""
    notes_val = st.text_area(
        t("notes", lang),
        height=160,
        key="custom_notes_area",
        placeholder=t("notes_empty", lang),
    )
    p.custom_notes = notes_val
    if st.button(t("save_notes", lang), type="primary", use_container_width=True, key="save_notes_btn"):
        if st.session_state.get("user_id"):
            persist_user_data()
        st.success(t("notes_saved", lang))


def render_tasks_page(lang: Lang) -> None:
    """UI-06 / UI-11: task page + Moodle .ics import (no SSO / no authtoken storage)."""
    from core.moodle_ics import (
        MOODLE_CALENDAR,
        MOODLE_HOME,
        merge_moodle_tasks,
        parse_ics_tasks,
    )

    p: StudentProfile = st.session_state.profile
    st.markdown(
        f'<div class="bu-workspace-head"><h3>{html.escape(t("nav_tasks", lang))}</h3></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="margin:0 0 0.75rem;font-size:13px">'
        f'<a href="{html.escape(MOODLE_HOME)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(t("moodle_open", lang))}</a>'
        f' · '
        f'<a href="{html.escape(MOODLE_CALENDAR)}" target="_blank" rel="noopener noreferrer">'
        f'Calendar</a></p>',
        unsafe_allow_html=True,
    )

    with st.expander(t("moodle_section", lang), expanded=not p.tasks):
        st.caption(t("moodle_hint", lang))
        st.markdown(t("moodle_steps", lang))
        ics_file = st.file_uploader(
            t("moodle_upload", lang),
            type=["ics"],
            key="moodle_ics_upload",
        )
        replace_moodle = st.checkbox(
            t("moodle_replace", lang), value=True, key="moodle_replace_prev"
        )
        if st.button(t("moodle_import", lang), type="primary", use_container_width=True, key="moodle_import_btn"):
            if not ics_file:
                st.warning(t("moodle_upload", lang))
            else:
                incoming = parse_ics_tasks(ics_file.getvalue())
                if not incoming:
                    st.warning(t("moodle_none", lang))
                else:
                    merged, added = merge_moodle_tasks(
                        p.tasks, incoming, replace_moodle=replace_moodle
                    )
                    p.tasks = merged
                    persist_user_data()
                    st.success(t("moodle_imported", lang, n=added))
                    st.rerun()

    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        new_task = st.text_input(
            t("new_task", lang),
            key="tasks_page_new_task",
            label_visibility="collapsed",
            placeholder=t("new_task", lang),
        )
    with c2:
        new_due = st.text_input(
            t("new_due", lang),
            key="tasks_page_new_due",
            label_visibility="collapsed",
            placeholder=t("new_due", lang),
        )
    with c3:
        add_clicked = st.button(
            t("add_task", lang), type="primary", use_container_width=True, key="tasks_page_add"
        )
    if add_clicked:
        if new_task.strip():
            p.tasks.append(TaskItem(title=new_task.strip(), due=new_due.strip(), source="manual"))
            persist_user_data()
            st.success(t("task_added", lang))
            st.rerun()
        else:
            st.warning(t("new_task", lang))

    if not p.tasks:
        st.caption(t("today_no_tasks", lang))
        return

    for i, task in enumerate(list(p.tasks)):
        left, mid, right = st.columns([4.2, 1.4, 1])
        with left:
            due = task.due or "—"
            badge = f" · `{t('moodle_badge', lang)}`" if (task.source or "") == "moodle" else ""
            course = f" · {task.course}" if task.course else ""
            st.markdown(
                f"**{html.escape(due)}** · {html.escape(task.title)}{html.escape(course)}{badge}"
            )
        with mid:
            if (task.url or "").startswith("http"):
                st.link_button(
                    t("moodle_open_item", lang),
                    task.url,
                    use_container_width=True,
                )
        with right:
            if st.button(t("delete_task", lang), key=f"del_task_{i}", use_container_width=True):
                del p.tasks[i]
                persist_user_data()
                st.rerun()


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
                            set_nav_page("chat")
                            st.session_state._scroll_chat = True
                            st.rerun()
                        else:
                            st.warning(friendly_vision_error(lang, kind="tt"))
                    except Exception:
                        st.error(friendly_vision_error(lang, kind="tt"))
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
                        set_nav_page("chat")
                        st.session_state._scroll_chat = True
                        st.rerun()
                    except Exception:
                        st.error(friendly_vision_error(lang, kind="mail"))
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

    # task — deep-link from extension lands on tasks page tooling
    set_nav_page("tasks")
    st.session_state.fab_panel = None
    st.rerun()


def consume_bubble_pick_query(prompts: list[str], *, plan_index: int | None) -> None:
    pick = st.session_state.pop("_pending_pick", None)
    if pick is None:
        pick = _qp_one(st.query_params.get("pick"))
        if pick is not None:
            try:
                del st.query_params["pick"]
            except Exception:
                pass
    if pick is None:
        return
    try:
        idx = int(pick)
    except ValueError:
        return
    if plan_index is not None and idx == plan_index:
        st.session_state.pending_plan = True
    elif 0 <= idx < len(prompts):
        st.session_state.pending_prompt = prompts[idx]


def render_home_facts_strip(lang: Lang) -> None:
    """Compact live facts under the chat guide (HKO + official links)."""
    weather = fetch_weather(lang)
    links = " · ".join(
        f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">'
        f"{html.escape(label)}</a>"
        for label, url in official_links(lang)[:3]
    )
    st.markdown(
        f'<div class="bu-card" style="margin-top:0.5rem">'
        f'<p style="margin:0;font-size:12px;color:var(--text-soft)">{html.escape(t("home_facts_title", lang))}</p>'
        f'<p style="margin:0.35rem 0 0;font-size:14px;color:var(--text)">'
        f"{html.escape(weather.one_line(lang))}</p>"
        f'<p style="margin:0.45rem 0 0;font-size:12px">{links}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_rag_citations(lang: Lang) -> None:
    cites = st.session_state.get("_last_rag_citations") or []
    if not cites:
        return
    with st.expander(t("rag_sources_title", lang), expanded=False):
        for name in cites[:8]:
            st.caption(f"· {name}")
        st.caption(f"{t('link_hko', lang)} — {HKO_HOME}")
        st.caption(f"{t('link_ar_calendar', lang)} — {AR_CALENDAR}")


def main_chat(lang: Lang) -> None:
    """UI-05: stage is conversation + bottom input only."""
    p: StudentProfile = st.session_state.profile
    settings = get_app_settings()
    messages = st.session_state.messages
    pristine = not chat_has_user_turn(messages)
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

    pristine = not chat_has_user_turn(st.session_state.messages)
    inject_ui_phase("chat")

    if pristine and not st.session_state.get("agent_burst"):
        st.markdown(
            f'<div class="bu-chat-guide">'
            f'<p class="bu-chat-guide-name">{html.escape(bot_nick(lang))}</p>'
            f'<p class="bu-chat-guide-hint">{html.escape(t("chat_empty_guide", lang))}</p>'
            f"</div>",
            unsafe_allow_html=True,
        )
        render_home_facts_strip(lang)
    elif pristine and st.session_state.get("agent_burst"):
        render_mini_prompt_bubbles(
            prompts,
            plan_label=t("plan_week", lang),
            hint=t("burst_pick_hint", lang),
            auth_token=auth_token,
            ui_lang=lang,
        )
    else:
        render_chat_thread(messages)
        render_rag_citations(lang)

    if st.session_state.pop("_scroll_chat", None):
        scroll_latest_assistant_into_view()

    pending = st.session_state.pop("pending_prompt", None)
    user_input = st.chat_input(t("chat_placeholder", lang))
    if pending:
        user_input = pending

    if user_input:
        st.session_state.agent_burst = True
        set_nav_page("chat")
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] in ("user", "assistant")
        ]
        st.session_state.messages.append({"role": "user", "content": user_input})
        if not pristine:
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
        bundle = get_last_retrieval()
        if bundle is not None:
            st.session_state._last_rag_citations = list(bundle.citations)
        if not isinstance(reply, str):
            reply = "" if reply is None else str(reply)
        reply = reply.strip() or t("chat_empty_reply", lang)
        welcomes = all_welcome_bodies()
        st.session_state.messages = [
            m
            for m in st.session_state.messages
            if not (m.get("role") == "assistant" and m.get("content") in welcomes)
        ]
        st.session_state.messages.append({"role": "assistant", "content": reply})
        persist_user_data()
        st.session_state._scroll_chat = True
        st.rerun()


def main() -> None:
    load_server_secrets()
    init_db()
    restore_lang_from_query()
    lang = get_lang()

    restore_auth_from_query()
    capture_nav_intents()

    if not st.session_state.get("user_id"):
        ensure_lang_query_param(lang)
        inject_chunk_recovery()
        inject_bu_theme(get_app_settings())
        # Login: no dual-rail chrome — card only (UI-08).
        login_screen(lang)
        return

    init_state(lang)
    if st.session_state.get("user_id") and st.session_state.get("_ui_revision") != _UI_REVISION:
        st.session_state._ui_revision = _UI_REVISION
        st.session_state._db_loaded = False
    load_user_data_once(lang)
    lang = get_lang()
    apply_nav_intents()
    if "messages" not in st.session_state:
        st.session_state.messages = default_welcome(lang)
    if "app_settings" not in st.session_state and "profile" in st.session_state:
        st.session_state.app_settings = AppSettings.from_dict(st.session_state.profile.settings)

    ensure_auth_query_param()
    ensure_lang_query_param(lang)
    inject_chunk_recovery()
    inject_bu_theme(get_app_settings())
    lang = render_app_sidebar(lang)

    # Route fab deep-links to the right page before stage render.
    fab = st.session_state.get("fab_panel")
    if fab == "task":
        set_nav_page("tasks")
        st.session_state.fab_panel = None
    elif fab == "tt":
        set_nav_page("workspace")
        st.session_state.ws_seg = t("ws_seg_timetable", lang)
        # keep fab panel for one-shot OR clear and use workspace — use workspace seg
        st.session_state.fab_panel = None
    elif fab == "mail":
        set_nav_page("workspace")
        st.session_state.ws_seg = t("ws_seg_mail", lang)
        st.session_state.fab_panel = None

    page = ensure_nav_page()
    if page == "workspace":
        render_workspace_panel(lang)
    elif page == "tasks":
        render_tasks_page(lang)
    else:
        main_chat(lang)


if __name__ == "__main__":
    main()

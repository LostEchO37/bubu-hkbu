"""Bot nickname & project credit — one place for brand voice."""

from __future__ import annotations

from core.i18n import Lang

# 阿Bu = Ah Bu — short, campus-y, tied to HKBU / BU
BOT_NICK: dict[Lang, str] = {
    "zh-CN": "阿Bu",
    "zh-TW": "阿Bu",
    "en": "BuBu",
}

BOT_TAGLINE: dict[Lang, str] = {
    "zh-CN": "浸大同学助手",
    "zh-TW": "浸大同學助手",
    "en": "HKBU buddy assistant",
}

PROJECT_CREDIT = "proudly presented by GTSC2066 Group 16"


def bot_nick(lang: Lang) -> str:
    return BOT_NICK.get(lang, BOT_NICK["zh-CN"])


def bot_intro(lang: Lang) -> str:
    nick = bot_nick(lang)
    tag = BOT_TAGLINE.get(lang, BOT_TAGLINE["zh-CN"])
    return f"{nick} · {tag}"

"""Playful, time-aware homepage copy."""

from __future__ import annotations

import random
from datetime import datetime

from core.i18n import Lang


def time_greeting(lang: Lang) -> str:
    hour = datetime.now().hour
    if lang == "en":
        if hour < 12:
            return "Good morning"
        if hour < 18:
            return "Good afternoon"
        return "Good evening"
    if lang == "zh-TW":
        if hour < 11:
            return "早晨呀"
        if hour < 14:
            return "中午好"
        if hour < 18:
            return "下午好"
        return "晚上好"
    if hour < 11:
        return "早上好呀"
    if hour < 14:
        return "中午好"
    if hour < 18:
        return "下午好"
    return "晚上好"


def fun_subline(lang: Lang, name: str = "") -> str:
    nick = name.strip() or {"zh-CN": "同学", "zh-TW": "同學", "en": "there"}[lang]
    tips = {
        "zh-CN": [
            f"{nick}，今天也要元气满满～ 📚",
            "考期将近？我可以帮你排复习档期 ✨",
            "上传课表截图，我帮你看哪天能摸鱼（误）",
            "BUniPort 太绕？校园问题先来问我 🎓",
        ],
        "zh-TW": [
            f"{nick}，今日都要加油～ 📚",
            "考期將至？我可以幫你排複習檔期 ✨",
            "上傳課表截圖，我幫你睇邊日得閒",
            "BUniPort 太複雜？校園問題先問我 🎓",
        ],
        "en": [
            f"Hey {nick}, let's make today productive 📚",
            "Exams coming? I'll help you block revision time ✨",
            "Drop a timetable screenshot — I'll read it for you",
            "Campus questions? Ask me before digging through portals 🎓",
        ],
    }
    return random.choice(tips[lang])

"""User-facing display & personality preferences."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

FontSize = Literal["small", "medium", "large"]
ThemeMode = Literal["light", "dark"]
Personality = Literal["playful", "balanced", "calm"]
UiLang = Literal["zh-CN", "zh-TW", "en"]

FONT_PX = {"small": "14px", "medium": "16px", "large": "18px"}
HERO_SCALE = {"small": "1.45rem", "medium": "1.65rem", "large": "1.85rem"}
_VALID_LANG = {"zh-CN", "zh-TW", "en"}


@dataclass
class AppSettings:
    font_size: FontSize = "medium"
    theme: ThemeMode = "light"
    personality: Personality = "playful"
    ui_lang: UiLang = "zh-CN"

    def to_dict(self) -> dict[str, str]:
        return {
            "font_size": self.font_size,
            "theme": self.theme,
            "personality": self.personality,
            "ui_lang": self.ui_lang,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AppSettings:
        if not data:
            return cls()
        raw_lang = data.get("ui_lang", "zh-CN")
        ui_lang: UiLang = raw_lang if raw_lang in _VALID_LANG else "zh-CN"  # type: ignore[assignment]
        return cls(
            font_size=data.get("font_size", "medium"),  # type: ignore[arg-type]
            theme=data.get("theme", "light"),  # type: ignore[arg-type]
            personality=data.get("personality", "playful"),  # type: ignore[arg-type]
            ui_lang=ui_lang,
        )


def temperature_for(personality: Personality) -> float:
    return {"playful": 0.78, "balanced": 0.68, "calm": 0.52}[personality]

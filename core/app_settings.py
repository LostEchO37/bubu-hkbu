"""User-facing display & personality preferences."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

FontSize = Literal["small", "medium", "large"]
ThemeMode = Literal["light", "dark"]
Personality = Literal["playful", "balanced", "calm"]

FONT_PX = {"small": "14px", "medium": "16px", "large": "18px"}
HERO_SCALE = {"small": "1.45rem", "medium": "1.65rem", "large": "1.85rem"}


@dataclass
class AppSettings:
    font_size: FontSize = "medium"
    theme: ThemeMode = "light"
    personality: Personality = "playful"

    def to_dict(self) -> dict[str, str]:
        return {
            "font_size": self.font_size,
            "theme": self.theme,
            "personality": self.personality,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AppSettings:
        if not data:
            return cls()
        return cls(
            font_size=data.get("font_size", "medium"),  # type: ignore[arg-type]
            theme=data.get("theme", "light"),  # type: ignore[arg-type]
            personality=data.get("personality", "playful"),  # type: ignore[arg-type]
        )


def temperature_for(personality: Personality) -> float:
    return {"playful": 0.78, "balanced": 0.68, "calm": 0.52}[personality]

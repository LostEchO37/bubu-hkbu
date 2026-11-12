"""Live campus-adjacent facts from official open APIs (HKO, etc.).

Network failures are soft — UI and chat keep working with cached/empty facts.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

from core.i18n import Lang, t

HKO_WEATHER_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
HKO_HOME = "https://www.hko.gov.hk/"
AR_CALENDAR = "https://calendar.ar.hkbu.edu.hk/"
# Prefer stations near Kowloon Tong / Sha Tin (HKBU campus area).
_TEMP_PREF = (
    "沙田",
    "Sha Tin",
    "九龙城",
    "九龍城",
    "Kowloon City",
    "京士柏",
    "King's Park",
    "香港天文台",
    "Hong Kong Observatory",
)

_CACHE_TTL_SEC = 15 * 60
_cache: dict[str, tuple[float, Any]] = {}


@dataclass
class WeatherSnapshot:
    ok: bool
    temp_c: int | None = None
    temp_place: str = ""
    humidity: int | None = None
    forecast: str = ""
    outlook: str = ""
    warnings: list[str] = field(default_factory=list)
    update_time: str = ""
    icon: int | None = None
    source_url: str = HKO_HOME
    error: str = ""

    def one_line(self, lang: Lang) -> str:
        if not self.ok:
            return t("weather_unavailable", lang)
        parts: list[str] = []
        if self.temp_c is not None:
            place = self.temp_place or t("weather_place_fallback", lang)
            parts.append(f"{place} {self.temp_c}°C")
        if self.humidity is not None:
            parts.append(t("weather_humidity", lang, n=self.humidity))
        if self.forecast:
            short = self.forecast.strip().replace("\n", " ")
            if len(short) > 42:
                short = short[:40] + "…"
            parts.append(short)
        if self.warnings:
            parts.append(t("weather_warning_on", lang))
        return " · ".join(parts) if parts else t("weather_unavailable", lang)

    def llm_block(self) -> str:
        if not self.ok:
            return "## 实时天气\n- （香港天文台暂不可用，勿编造气温）"
        lines = [
            "## 实时天气（香港天文台开放数据）",
            f"- 来源: {HKO_HOME}",
            f"- 更新: {self.update_time or '—'}",
        ]
        if self.temp_c is not None:
            lines.append(f"- 气温: {self.temp_c}°C @ {self.temp_place or '—'}")
        if self.humidity is not None:
            lines.append(f"- 相对湿度: {self.humidity}%")
        if self.forecast:
            lines.append(f"- 本港预报: {self.forecast.strip()}")
        if self.outlook:
            lines.append(f"- 展望: {self.outlook.strip()[:200]}")
        if self.warnings:
            for w in self.warnings[:4]:
                lines.append(f"- 警告: {w}")
        else:
            lines.append("- 警告: 暂无生效警告摘要")
        lines.append("- 硬性: 天气数字只能引用本块；过期或缺失时说明以天文台官网为准。")
        return "\n".join(lines)


def _hko_lang(lang: Lang) -> str:
    if lang == "zh-TW":
        return "tc"
    if lang == "en":
        return "en"
    return "sc"


def _cache_get(key: str) -> Any | None:
    row = _cache.get(key)
    if not row:
        return None
    ts, val = row
    if time.time() - ts > _CACHE_TTL_SEC:
        return None
    return val


def _cache_set(key: str, val: Any) -> None:
    _cache[key] = (time.time(), val)


def _http_json(url: str, params: dict[str, str], *, timeout: float = 6.0) -> dict[str, Any]:
    full = f"{url}?{urlencode(params)}"
    req = urllib.request.Request(
        full,
        headers={"User-Agent": "BuBu-HKBU-Assistant/1.0 (campus student project)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — official HKO HTTPS
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def _pick_temp(data: dict[str, Any]) -> tuple[int | None, str]:
    rows = (data.get("temperature") or {}).get("data") or []
    if not isinstance(rows, list) or not rows:
        return None, ""
    by_place = {str(r.get("place", "")): r for r in rows if isinstance(r, dict)}
    for pref in _TEMP_PREF:
        if pref in by_place:
            try:
                return int(by_place[pref]["value"]), pref
            except (TypeError, ValueError, KeyError):
                continue
    first = rows[0]
    try:
        return int(first.get("value")), str(first.get("place") or "")
    except (TypeError, ValueError):
        return None, str(first.get("place") or "")


def _pick_humidity(data: dict[str, Any]) -> int | None:
    rows = (data.get("humidity") or {}).get("data") or []
    if not isinstance(rows, list) or not rows:
        return None
    try:
        return int(rows[0].get("value"))
    except (TypeError, ValueError):
        return None


def _as_str_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif isinstance(item, dict):
                name = item.get("name") or item.get("code") or item.get("type")
                if name:
                    out.append(str(name))
        return out
    if isinstance(value, dict):
        # warnsum: { WFIRE: {name, code, ...}, ... }
        out = []
        for meta in value.values():
            if isinstance(meta, dict):
                name = meta.get("name") or meta.get("type") or meta.get("code")
                if name:
                    out.append(str(name))
        return out
    return []


def fetch_weather(lang: Lang = "zh-CN", *, force: bool = False) -> WeatherSnapshot:
    """Current weather + local forecast from HKO open data."""
    key = f"weather:{_hko_lang(lang)}"
    if not force:
        hit = _cache_get(key)
        if isinstance(hit, WeatherSnapshot):
            return hit

    hlang = _hko_lang(lang)
    try:
        current = _http_json(HKO_WEATHER_URL, {"dataType": "rhrread", "lang": hlang})
        forecast = _http_json(HKO_WEATHER_URL, {"dataType": "flw", "lang": hlang})
        warnsum: dict[str, Any] = {}
        try:
            warnsum = _http_json(HKO_WEATHER_URL, {"dataType": "warnsum", "lang": hlang})
        except Exception:
            warnsum = {}

        temp_c, place = _pick_temp(current)
        humidity = _pick_humidity(current)
        warnings = _as_str_list(current.get("warningMessage")) + _as_str_list(warnsum)
        # de-dupe keep order
        seen: set[str] = set()
        uniq_warn: list[str] = []
        for w in warnings:
            if w not in seen:
                seen.add(w)
                uniq_warn.append(w)

        icons = current.get("icon") or []
        icon = int(icons[0]) if isinstance(icons, list) and icons else None
        snap = WeatherSnapshot(
            ok=True,
            temp_c=temp_c,
            temp_place=place,
            humidity=humidity,
            forecast=str(forecast.get("forecastDesc") or "").strip(),
            outlook=str(forecast.get("outlook") or "").strip(),
            warnings=uniq_warn,
            update_time=str(current.get("updateTime") or forecast.get("updateTime") or ""),
            icon=icon,
        )
        _cache_set(key, snap)
        return snap
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError) as exc:
        fail = WeatherSnapshot(ok=False, error=str(exc)[:120])
        # Short negative cache so a downed API does not hammer every rerun.
        _cache_set(key, fail)
        return fail


def official_links(lang: Lang) -> list[tuple[str, str]]:
    """Label + URL pairs for sidebar / empty-state."""
    from core.moodle_ics import MOODLE_HOME

    return [
        (t("link_moodle", lang), MOODLE_HOME),
        (t("link_hko", lang), HKO_HOME),
        (t("link_ar_calendar", lang), AR_CALENDAR),
        (t("link_hkbu_home", lang), "https://www.hkbu.edu.hk/"),
    ]


def live_facts_for_llm(lang: Lang = "zh-CN") -> str:
    weather = fetch_weather(lang)
    links = "\n".join(f"- {label}: {url}" for label, url in official_links(lang))
    return f"{weather.llm_block()}\n\n## 官方链接\n{links}"

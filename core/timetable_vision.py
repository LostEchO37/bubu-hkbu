"""Extract timetable from screenshot via multimodal LLM."""

from __future__ import annotations

import base64
import io
import json
import os
import re

from core.agent import _client
from core.profile import CourseSlot


EXTRACT_PROMPT = """You are reading an HKBU weekly timetable screenshot (grid: Mon–Sat columns, time rows).
List EVERY class block. Return ONLY compact JSON — no markdown, no commentary:
{"courses":[{"course_code":"GTSC2066","course_name":"","day":"Wed","start_time":"14:30","end_time":"16:20","location":"FSC801C"}]}
Rules:
- day: Mon Tue Wed Thu Fri Sat Sun
- times: 24h HH:MM (infer end from block height / next boundary)
- HKBU grid convention: classes START at xx:30 and END at xx:20 (never xx:30 end).
  Examples: 09:30-10:20, 09:30-11:20, 14:30-16:20. Break between back-to-back slots is 10 minutes.
- course_code from the blue cell (e.g. GFQR1026); ignore section numbers like (00003) in course_code
- location: room codes (OEE1017, WLB204, FSC801C…). Multiple rooms → join with ", "
- course_name may be ""
- empty grid → {"courses":[]}
Keep the JSON short. Do not wrap in ```.
"""

RETRY_PROMPT = """Same image. Output ONLY one minified JSON object with key "courses".
No prose. No code fences. Close all brackets/strings.
HKBU times: start xx:30, end xx:20 (e.g. 09:30-11:20).
Example shape: {"courses":[{"course_code":"X","course_name":"","day":"Tue","start_time":"09:30","end_time":"10:20","location":"OEE1017"}]}
"""


def _vision_model() -> str:
    return os.environ.get("OPENAI_VISION_MODEL", "").strip() or os.environ.get(
        "OPENAI_MODEL", "gemini-3.8-flash"
    )


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _repair_json_text(text: str) -> str:
    """Best-effort repair for truncated model JSON (unterminated string / missing braces)."""
    text = _strip_fences(text)
    start = text.find("{")
    if start < 0:
        return text
    text = text[start:]

    # Close an open string if truncated mid-value
    in_str = False
    escape = False
    for ch in text:
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
    if in_str:
        text += '"'

    # Drop trailing incomplete object fragment after last complete course
    # e.g. ..., {"course_code": "AB
    if text.count("{") > text.count("}"):
        # Prefer cutting back to last complete `}`
        last = text.rfind("}")
        if last > 0:
            text = text[: last + 1]

    # Balance braces / brackets
    stack: list[str] = []
    in_str = False
    escape = False
    for ch in text:
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack and stack[-1] == ch:
            stack.pop()
    while stack:
        text += stack.pop()

    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text


def _courses_from_loose_objects(text: str) -> list[dict]:
    """Pull individual course-like objects if the outer JSON is beyond repair."""
    objs = re.findall(
        r'\{[^{}]*"course_code"\s*:\s*"[^"]+"[^{}]*\}',
        text,
        flags=re.DOTALL,
    )
    out: list[dict] = []
    for raw in objs:
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return out


def _parse_courses_payload(text: str) -> list[dict]:
    cleaned = _strip_fences(text)
    candidates = [cleaned, _repair_json_text(cleaned)]
    # Also try substring from first { to last }
    a, b = cleaned.find("{"), cleaned.rfind("}")
    if a >= 0 and b > a:
        candidates.append(cleaned[a : b + 1])
        candidates.append(_repair_json_text(cleaned[a : b + 1]))

    for cand in candidates:
        try:
            data = json.loads(cand)
            if isinstance(data, dict) and isinstance(data.get("courses"), list):
                return [c for c in data["courses"] if isinstance(c, dict)]
            if isinstance(data, list):
                return [c for c in data if isinstance(c, dict)]
        except json.JSONDecodeError:
            continue

    loose = _courses_from_loose_objects(cleaned)
    if loose:
        return loose
    raise json.JSONDecodeError("Could not parse timetable JSON", cleaned, 0)


def _normalize_day(day: str) -> str:
    d = day.strip()
    aliases = {
        "monday": "Mon",
        "tuesday": "Tue",
        "wednesday": "Wed",
        "thursday": "Thu",
        "friday": "Fri",
        "saturday": "Sat",
        "sunday": "Sun",
        "周一": "Mon",
        "周二": "Tue",
        "周三": "Wed",
        "周四": "Thu",
        "周五": "Fri",
        "周六": "Sat",
        "周日": "Sun",
        "一": "Mon",
        "二": "Tue",
        "三": "Wed",
        "四": "Thu",
        "五": "Fri",
        "六": "Sat",
        "日": "Sun",
    }
    key = d.lower()
    if key in aliases:
        return aliases[key]
    if d[:3].title() in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}:
        return d[:3].title()
    return d[:3].title() if d else ""


def _norm_time(raw: str) -> str:
    raw = raw.strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", raw)
    if not m:
        return raw
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def _snap_hkbu_times(start: str, end: str) -> tuple[str, str]:
    """HKBU periods start xx:30 and end xx:20; fix common OCR end=:30 mistakes."""
    sm = re.match(r"^(\d{2}):(\d{2})$", start)
    em = re.match(r"^(\d{2}):(\d{2})$", end)
    if not sm or not em:
        return start, end
    sh, smin = int(sm.group(1)), int(sm.group(2))
    eh, emin = int(em.group(1)), int(em.group(2))
    # Vision often writes the next slot start (xx:30) as end instead of xx:20
    if emin == 30:
        end = f"{eh:02d}:20"
        emin = 20
    # e.g. 09:20-11:20 → likely 09:30-11:20
    if smin == 20 and emin == 20 and eh > sh:
        start = f"{sh:02d}:30"
    return start, end


def _slots_from_courses(courses: list[dict]) -> list[CourseSlot]:
    slots: list[CourseSlot] = []
    seen: set[tuple[str, str, str, str]] = set()
    for c in courses:
        code = str(c.get("course_code", "")).strip()
        # Drop trailing section like (00003) if model glued it on
        code = re.sub(r"\s*\(\d+\)\s*$", "", code)
        day = _normalize_day(str(c.get("day", "") or ""))
        start = _norm_time(str(c.get("start_time", "")).strip())
        end = _norm_time(str(c.get("end_time", "")).strip())
        start, end = _snap_hkbu_times(start, end)
        loc = str(c.get("location", "")).strip()
        name = str(c.get("course_name", "")).strip()
        if not day or not start:
            continue
        key = (day, start, end, code)
        if key in seen:
            continue
        seen.add(key)
        slots.append(
            CourseSlot(
                course_code=code,
                course_name=name,
                day=day,
                start_time=start,
                end_time=end,
                location=loc,
            )
        )
    day_order = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
    slots.sort(key=lambda s: (day_order.get(s.day, 9), s.start_time, s.course_code))
    return slots


def _prepare_image(image_bytes: bytes, mime: str) -> tuple[bytes, str]:
    """Downscale & JPEG-compress for faster, more reliable vision calls."""
    try:
        from PIL import Image
    except ImportError:
        return image_bytes, mime

    try:
        im = Image.open(io.BytesIO(image_bytes))
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        elif im.mode == "L":
            im = im.convert("RGB")
        w, h = im.size
        max_edge = 1600
        scale = min(1.0, max_edge / max(w, h))
        if scale < 1.0:
            im = im.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
        # Mild contrast bump helps grid OCR on washed screenshots
        from PIL import ImageEnhance

        im = ImageEnhance.Contrast(im).enhance(1.12)
        im = ImageEnhance.Sharpness(im).enhance(1.08)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=88, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, mime


def _call_vision(image_data_url: str, prompt: str, *, max_tokens: int) -> str:
    client = _client()
    model = _vision_model()
    kwargs: dict = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    # Some OpenAI-compatible gateways support this; ignore if rejected upstream.
    try:
        resp = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
    except Exception:
        resp = client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def parse_timetable_from_image(image_bytes: bytes, mime: str = "image/png") -> list[CourseSlot]:
    image_bytes, mime = _prepare_image(image_bytes, mime)
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"

    raw = _call_vision(data_url, EXTRACT_PROMPT, max_tokens=4096)
    try:
        courses = _parse_courses_payload(raw)
    except json.JSONDecodeError:
        raw = _call_vision(data_url, RETRY_PROMPT, max_tokens=4096)
        courses = _parse_courses_payload(raw)

    return _slots_from_courses(courses)

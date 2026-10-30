"""Read an email screenshot and draft a reply (no mailbox connection)."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field

from core.i18n import Lang
from core.timetable_vision import _call_vision, _prepare_image, _strip_fences


@dataclass
class MailDraftResult:
    subject: str = ""
    sender: str = ""
    date: str = ""
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    tasks: list[dict[str, str]] = field(default_factory=list)
    reply_subject: str = ""
    reply_body: str = ""


TONE_HINT = {
    "polite": "Polite, professional, student-to-staff or peer tone. Warm but formal enough for campus mail.",
    "concise": "Very concise. Short paragraphs. No fluff. Still polite.",
    "friendly": "Friendly classmate tone. Natural and clear, not slang-heavy.",
}

LANG_REPLY = {
    "zh-CN": "Write the reply_body in Simplified Chinese unless the email is clearly English-only.",
    "zh-TW": "Write the reply_body in Traditional Chinese unless the email is clearly English-only.",
    "en": "Write the reply_body in English unless the email is clearly Chinese-only (then match Chinese).",
}


def _extract_prompt(*, tone: str, lang: Lang) -> str:
    tone_h = TONE_HINT.get(tone, TONE_HINT["polite"])
    lang_h = LANG_REPLY.get(lang, LANG_REPLY["zh-CN"])
    return f"""You are helping an HKBU student. The image is a screenshot of an email (web/app mail).
Read the visible email (ignore browser chrome / ads). Return ONLY compact JSON — no markdown:
{{
  "subject":"",
  "from":"",
  "date":"",
  "summary":"",
  "key_points":[""],
  "tasks":[{{"title":"","due":""}}],
  "reply_subject":"Re: ...",
  "reply_body":""
}}
Rules:
- Extract subject/from/date if visible; else "".
- summary: 1–2 sentences of what the sender wants.
- key_points: up to 5 short bullets.
- tasks: deadlines/homework/meetings implied by the mail; due as YYYY-MM-DD if clear else "".
- reply_subject: Re: + subject (or a short apt subject).
- reply_body: a ready-to-send reply draft from the student. {tone_h}
- {lang_h}
- Do NOT invent facts not in the screenshot. If info is missing, acknowledge politely in the draft.
- Sign-off: leave a short placeholder like [Your name] if name unknown.
- No code fences. No commentary outside JSON.
"""


def _parse_payload(raw: str) -> MailDraftResult:
    text = _strip_fences(raw)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise json.JSONDecodeError("no object", text, 0)
    data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise json.JSONDecodeError("not object", text, 0)

    points = data.get("key_points") or []
    if isinstance(points, str):
        points = [points]
    tasks_raw = data.get("tasks") or []
    tasks: list[dict[str, str]] = []
    for item in tasks_raw:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        tasks.append({"title": title, "due": str(item.get("due") or "").strip()})

    body = str(data.get("reply_body") or "").strip()
    if not body:
        raise ValueError("empty reply_body")

    return MailDraftResult(
        subject=str(data.get("subject") or "").strip(),
        sender=str(data.get("from") or "").strip(),
        date=str(data.get("date") or "").strip(),
        summary=str(data.get("summary") or "").strip(),
        key_points=[str(p).strip() for p in points if str(p).strip()][:8],
        tasks=tasks[:12],
        reply_subject=str(data.get("reply_subject") or "").strip(),
        reply_body=body,
    )


def draft_reply_from_email_image(
    image_bytes: bytes,
    mime: str = "image/png",
    *,
    tone: str = "polite",
    lang: Lang = "zh-CN",
) -> MailDraftResult:
    image_bytes, mime = _prepare_image(image_bytes, mime)
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    prompt = _extract_prompt(tone=tone, lang=lang)

    raw = _call_vision(data_url, prompt, max_tokens=2500)
    try:
        return _parse_payload(raw)
    except (json.JSONDecodeError, ValueError):
        retry = (
            prompt
            + "\nRETRY: Output ONE minified JSON object only. reply_body must be non-empty."
        )
        raw = _call_vision(data_url, retry, max_tokens=2500)
        return _parse_payload(raw)


def format_draft_for_chat(result: MailDraftResult, lang: Lang = "zh-CN") -> str:
    labels = {
        "zh-CN": ("邮件摘要", "要点", "建议回复", "主题"),
        "zh-TW": ("郵件摘要", "要點", "建議回覆", "主題"),
        "en": ("Email summary", "Key points", "Suggested reply", "Subject"),
    }
    s, k, r, sub = labels.get(lang, labels["zh-CN"])
    lines = [f"**{s}**"]
    if result.subject:
        lines.append(f"- {sub}: {result.subject}")
    if result.sender:
        lines.append(f"- From: {result.sender}")
    if result.summary:
        lines.append(result.summary)
    if result.key_points:
        lines.append(f"\n**{k}**")
        for p in result.key_points:
            lines.append(f"- {p}")
    lines.append(f"\n**{r}**")
    if result.reply_subject:
        lines.append(f"`{result.reply_subject}`")
    lines.append("")
    lines.append(result.reply_body)
    return "\n".join(lines)

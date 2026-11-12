"""Parse Moodle / bueLearning calendar exports (.ics) into TaskItems.

Students export from Moodle Calendar → Export → courses / upcoming.
We never ask for SSO passwords or store Moodle authtoken URLs.
"""

from __future__ import annotations

import re
from datetime import datetime

from core.profile import TaskItem

MOODLE_HOME = "https://buelearning.hkbu.edu.hk/"
MOODLE_CALENDAR = "https://buelearning.hkbu.edu.hk/calendar/view.php?view=month"


def _unfold(ics_text: str) -> str:
    # RFC 5545 line folding: CRLF + space/tab continues the previous line
    return re.sub(r"\r?\n[ \t]", "", ics_text)


def _unescape(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
        .strip()
    )


def _field(block: str, name: str) -> str:
    """Return first property value for NAME (handles NAME;PARAM=...:value)."""
    pat = re.compile(rf"^{re.escape(name)}[;:](.*)$", re.I | re.M)
    m = pat.search(block)
    if not m:
        return ""
    raw = m.group(1)
    if ":" in raw and m.group(0).upper().startswith(name.upper() + ";"):
        raw = raw.split(":", 1)[-1]
    return _unescape(raw)


def _parse_ics_date(value: str) -> str:
    """Normalize DTSTART/DTEND/DUE to YYYY-MM-DD when possible."""
    v = (value or "").strip()
    if not v:
        return ""
    # Strip trailing Z / timezone suffixes for date-only compare
    v = v.replace("Z", "")
    if "T" in v:
        head = v.split("T", 1)[0]
    else:
        head = v[:8] if re.fullmatch(r"\d{8}", v[:8] or "") else v
    if re.fullmatch(r"\d{8}", head):
        return f"{head[0:4]}-{head[4:6]}-{head[6:8]}"
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(head[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return head[:10]


def _guess_course(summary: str, description: str) -> str:
    blob = f"{summary} {description}"
    # Common Moodle patterns: "COMP1005: Essay" or course id in brackets
    m = re.search(r"\b([A-Z]{2,4}\s?\d{4}[A-Z]?)\b", blob)
    if m:
        return re.sub(r"\s+", "", m.group(1))
    m = re.search(r"Course(?:\s*short\s*name)?\s*[:=]\s*([^\n]+)", blob, re.I)
    if m:
        return m.group(1).strip()[:40]
    return ""


def parse_ics_tasks(data: bytes | str, *, source: str = "moodle") -> list[TaskItem]:
    """Extract VEVENT rows that look like deadlines / course events."""
    if isinstance(data, bytes):
        text = data.decode("utf-8", errors="replace")
    else:
        text = data
    text = _unfold(text)
    events = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, flags=re.I | re.S)
    out: list[TaskItem] = []
    seen: set[tuple[str, str]] = set()
    for block in events:
        summary = _field(block, "SUMMARY")
        if not summary:
            continue
        due = (
            _parse_ics_date(_field(block, "DUE"))
            or _parse_ics_date(_field(block, "DTSTART"))
            or _parse_ics_date(_field(block, "DTEND"))
        )
        description = _field(block, "DESCRIPTION")
        url = _field(block, "URL")
        # Skip pure empty placeholders
        key = (summary.strip().lower(), due)
        if key in seen:
            continue
        seen.add(key)
        course = _guess_course(summary, description)
        notes = ""
        if description:
            notes = re.sub(r"\s+", " ", description).strip()[:280]
        out.append(
            TaskItem(
                title=summary[:200],
                due=due,
                course=course,
                notes=notes,
                source=source,
                url=url[:500] if url else "",
            )
        )
    # Soonest first when dates exist
    out.sort(key=lambda t: (t.due or "9999", t.title.lower()))
    return out


def merge_moodle_tasks(
    existing: list[TaskItem],
    incoming: list[TaskItem],
    *,
    replace_moodle: bool = True,
) -> tuple[list[TaskItem], int]:
    """Merge imported Moodle tasks. Returns (new_list, added_count)."""
    if replace_moodle:
        kept = [t for t in existing if (t.source or "") != "moodle"]
    else:
        kept = list(existing)
    existing_keys = {(t.title.strip().lower(), (t.due or "").strip()) for t in kept}
    added = 0
    for item in incoming:
        key = (item.title.strip().lower(), (item.due or "").strip())
        if key in existing_keys:
            continue
        kept.append(item)
        existing_keys.add(key)
        added += 1
    return kept, added

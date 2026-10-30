"""Today view, exam countdown, and rush / conflict reminders."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from core.i18n import Lang, t
from core.profile import CourseSlot, StudentProfile, free_gaps, _from_minutes, _to_minutes

DAY_CODES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Hard-coded from AR 2026–27 calendar (zh knowledge file).
CALENDAR_EVENTS: list[dict] = [
    {
        "key": "exam_sem1",
        "start": date(2026, 12, 7),
        "end": date(2026, 12, 19),
    },
    {
        "key": "last_class_sem1",
        "start": date(2026, 11, 28),
        "end": date(2026, 11, 28),
    },
    {
        "key": "exam_sem2",
        "start": date(2027, 5, 13),
        "end": date(2027, 5, 17),
    },
    {
        "key": "last_class_sem2",
        "start": date(2027, 4, 24),
        "end": date(2027, 4, 24),
    },
]


@dataclass
class Reminder:
    kind: str  # rush | overlap
    text: str


def weekday_code(when: datetime | None = None) -> str:
    when = when or datetime.now()
    return DAY_CODES[when.weekday()]


def slots_on_day(profile: StudentProfile, day: str) -> list[CourseSlot]:
    return sorted(
        [s for s in profile.timetable if s.day == day],
        key=lambda s: s.start_time,
    )


def building_code(location: str) -> str:
    loc = (location or "").strip().upper()
    if not loc:
        return ""
    m = re.match(r"([A-Z]{2,4})", loc)
    return m.group(1) if m else loc[:3]


def next_class(
    profile: StudentProfile,
    *,
    now: datetime | None = None,
) -> tuple[CourseSlot | None, int | None]:
    """Return (next_or_current slot, minutes until start). Negative = already started."""
    now = now or datetime.now()
    day = weekday_code(now)
    now_m = now.hour * 60 + now.minute
    upcoming: list[tuple[int, CourseSlot]] = []
    for s in slots_on_day(profile, day):
        start = _to_minutes(s.start_time)
        end = _to_minutes(s.end_time)
        if start is None:
            continue
        if end is not None and end <= now_m:
            continue
        upcoming.append((start - now_m, s))
    if not upcoming:
        return None, None
    upcoming.sort(key=lambda x: x[0])
    delta, slot = upcoming[0]
    return slot, delta


@dataclass
class ClockStatus:
    """Authoritative now-vs-timetable snapshot for UI + LLM."""

    state: str  # in_class | soon | break | done | free_day | no_tt
    slot: CourseSlot | None
    minutes_to_start: int | None
    minutes_to_end: int | None
    free_from_hhmm: str  # earliest moment study can start from "now"


def clock_status(profile: StudentProfile, *, now: datetime | None = None) -> ClockStatus:
    now = now or datetime.now()
    now_m = now.hour * 60 + now.minute
    now_hhmm = f"{now.hour:02d}:{now.minute:02d}"

    if not profile.timetable:
        return ClockStatus("no_tt", None, None, None, now_hhmm)

    day_slots = slots_on_day(profile, weekday_code(now))
    if not day_slots:
        return ClockStatus("free_day", None, None, None, now_hhmm)

    slot, delta = next_class(profile, now=now)
    if slot is None or delta is None:
        return ClockStatus("done", None, None, None, now_hhmm)

    end_m = _to_minutes(slot.end_time)
    start_m = _to_minutes(slot.start_time)
    to_end = (end_m - now_m) if end_m is not None else None

    if delta < 0:
        # In class until end (:20). Study only after end_time — never "刚下课".
        free_from = slot.end_time if end_m is not None else now_hhmm
        return ClockStatus("in_class", slot, delta, to_end, free_from)
    if delta == 0:
        free_from = slot.end_time if end_m is not None else now_hhmm
        return ClockStatus("in_class", slot, 0, to_end, free_from)
    if delta <= 15:
        return ClockStatus("soon", slot, delta, to_end, now_hhmm)

    # Between classes or before first — free until this next start
    free_until = start_m
    if free_until is not None and free_until - now_m >= 1:
        return ClockStatus("break", slot, delta, to_end, now_hhmm)
    return ClockStatus("soon", slot, delta, to_end, now_hhmm)


def remaining_free_gaps(
    profile: StudentProfile,
    *,
    now: datetime | None = None,
    min_minutes: int = 30,
) -> list[tuple[str, str]]:
    """Today's free windows clipped to wall-clock (after current class if in one)."""
    now = now or datetime.now()
    day = weekday_code(now)
    status = clock_status(profile, now=now)
    free_from = _to_minutes(status.free_from_hhmm)
    if free_from is None:
        free_from = now.hour * 60 + now.minute

    out: list[tuple[str, str]] = []
    for d, a, b in free_gaps(profile, min_minutes=min_minutes):
        if d != day:
            continue
        a_m, b_m = _to_minutes(a), _to_minutes(b)
        if a_m is None or b_m is None:
            continue
        start = max(a_m, free_from)
        if b_m - start >= min_minutes:
            out.append((_from_minutes(start), _from_minutes(b_m)))
    return out


def remaining_week_gaps(
    profile: StudentProfile,
    *,
    now: datetime | None = None,
    min_minutes: int = 45,
) -> list[tuple[str, str, str]]:
    """Free windows from now through Sat (day, start, end)."""
    now = now or datetime.now()
    today = weekday_code(now)
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    try:
        idx = order.index(today)
    except ValueError:
        idx = 0

    rows: list[tuple[str, str, str]] = []
    # Today — clock-clipped
    for a, b in remaining_free_gaps(profile, now=now, min_minutes=min_minutes):
        rows.append((today, a, b))
    # Later weekdays — full gaps
    for day in order[idx + 1 :]:
        for d, a, b in free_gaps(profile, min_minutes=min_minutes):
            if d == day:
                rows.append((d, a, b))
    return rows


def today_free_gaps(profile: StudentProfile, *, now: datetime | None = None) -> list[tuple[str, str]]:
    """Sidebar display: remaining gaps from now (not past-morning free time)."""
    return remaining_free_gaps(profile, now=now, min_minutes=30)


def upcoming_tasks(profile: StudentProfile, *, limit: int = 4) -> list[str]:
    lines: list[str] = []
    for task in profile.tasks[:40]:
        due = (task.due or "").strip()
        title = task.title.strip()
        if not title:
            continue
        lines.append(f"{due or '—'}: {title}")
        if len(lines) >= limit:
            break
    return lines


def detect_reminders(profile: StudentProfile, *, lang: Lang = "zh-CN") -> list[Reminder]:
    """Overlaps + tight building changes (≤20 min between different buildings)."""
    out: list[Reminder] = []
    by_day: dict[str, list[CourseSlot]] = {}
    for s in profile.timetable:
        by_day.setdefault(s.day, []).append(s)

    for day, slots in by_day.items():
        ordered = sorted(slots, key=lambda s: (s.start_time, s.end_time))
        for i, a in enumerate(ordered):
            a0 = _to_minutes(a.start_time)
            a1 = _to_minutes(a.end_time)
            if a0 is None or a1 is None:
                continue
            for b in ordered[i + 1 :]:
                b0 = _to_minutes(b.start_time)
                b1 = _to_minutes(b.end_time)
                if b0 is None or b1 is None:
                    continue
                # Overlap
                if b0 < a1 and b1 > a0:
                    out.append(
                        Reminder(
                            kind="overlap",
                            text=t(
                                "remind_overlap",
                                lang,
                                day=day,
                                a=a.course_code or a.course_name or "?",
                                b=b.course_code or b.course_name or "?",
                                t1=f"{a.start_time}–{a.end_time}",
                                t2=f"{b.start_time}–{b.end_time}",
                            ),
                        )
                    )
                # Rush: HKBU break is typically 10 min (:20→:30). Cross-building
                # back-to-back still needs a walk warning; ignore same building.
                gap = b0 - a1
                if 0 <= gap <= 10:
                    ba, bb = building_code(a.location), building_code(b.location)
                    if ba and bb and ba != bb:
                        out.append(
                            Reminder(
                                kind="rush",
                                text=t(
                                    "remind_rush",
                                    lang,
                                    day=day,
                                    gap=gap,
                                    a=a.course_code or "?",
                                    from_b=a.location or ba,
                                    b=b.course_code or "?",
                                    to_b=b.location or bb,
                                ),
                            )
                        )
    # Dedupe
    seen: set[str] = set()
    uniq: list[Reminder] = []
    for r in out:
        if r.text in seen:
            continue
        seen.add(r.text)
        uniq.append(r)
    return uniq[:8]


def next_countdown_event(*, today: date | None = None) -> dict | None:
    today = today or date.today()
    best: dict | None = None
    best_delta = 10_000
    for ev in CALENDAR_EVENTS:
        start: date = ev["start"]
        end: date = ev["end"]
        if end < today:
            continue
        # Days until start (0 if ongoing)
        delta = 0 if start <= today <= end else (start - today).days
        if delta < best_delta:
            best_delta = delta
            best = {**ev, "days": delta, "ongoing": start <= today <= end}
    return best


def format_countdown(lang: Lang, *, today: date | None = None) -> tuple[str, str]:
    """Return (title, detail) for the countdown card."""
    ev = next_countdown_event(today=today)
    if not ev:
        return t("countdown_none", lang), ""
    key = ev["key"]
    label = t(f"countdown_{key}", lang)
    start, end = ev["start"], ev["end"]
    date_range = (
        f"{start.month}/{start.day}"
        if start == end
        else f"{start.month}/{start.day} – {end.month}/{end.day}"
    )
    if ev["ongoing"]:
        detail = t("countdown_ongoing", lang, label=label, dates=date_range)
    else:
        detail = t("countdown_in_days", lang, n=ev["days"], label=label, dates=date_range)
    return label, detail


def pulse_html(profile: StudentProfile, lang: Lang, *, now: datetime | None = None) -> str:
    """Compact sidebar card: today + countdown + reminders."""
    now = now or datetime.now()
    day = weekday_code(now)
    day_label = t(f"day_{day.lower()}", lang)
    slots = slots_on_day(profile, day)
    nxt, delta = next_class(profile, now=now)
    gaps = today_free_gaps(profile, now=now)
    reminders = detect_reminders(profile, lang=lang)
    cd_label, cd_detail = format_countdown(lang, today=now.date())
    tasks = upcoming_tasks(profile)

    # Today body
    if not profile.timetable:
        today_body = f'<p class="bu-pulse-muted">{html.escape(t("today_no_tt", lang))}</p>'
    elif not slots:
        today_body = f'<p class="bu-pulse-muted">{html.escape(t("today_free_day", lang))}</p>'
    else:
        parts = []
        if nxt is not None and delta is not None:
            if delta > 0:
                next_line = t(
                    "today_next_in",
                    lang,
                    n=delta,
                    code=nxt.course_code or "·",
                    time=nxt.start_time,
                    loc=nxt.location or "TBA",
                )
            elif delta == 0:
                next_line = t(
                    "today_next_now",
                    lang,
                    code=nxt.course_code or "·",
                    time=nxt.start_time,
                    loc=nxt.location or "TBA",
                )
            else:
                next_line = t(
                    "today_in_class",
                    lang,
                    code=nxt.course_code or "·",
                    end=nxt.end_time,
                    loc=nxt.location or "TBA",
                )
            parts.append(f'<p class="bu-pulse-next">{html.escape(next_line)}</p>')
        else:
            parts.append(
                f'<p class="bu-pulse-muted">{html.escape(t("today_done", lang))}</p>'
            )
        lis = []
        for s in slots:
            lis.append(
                "<li>"
                + html.escape(
                    f"{s.start_time}–{s.end_time} {s.course_code} @ {s.location or 'TBA'}"
                )
                + "</li>"
            )
        parts.append(f'<ul class="bu-pulse-list">{"".join(lis)}</ul>')
        if gaps:
            gtxt = " · ".join(f"{a}–{b}" for a, b in gaps[:3])
            parts.append(
                f'<p class="bu-pulse-gaps">{html.escape(t("today_gaps", lang, gaps=gtxt))}</p>'
            )
        today_body = "".join(parts)

    task_html = ""
    if tasks:
        items = "".join(f"<li>{html.escape(x)}</li>" for x in tasks)
        task_html = f'<ul class="bu-pulse-list tight">{items}</ul>'
    else:
        task_html = f'<p class="bu-pulse-muted">{html.escape(t("today_no_tasks", lang))}</p>'

    rem_html = ""
    if reminders:
        items = "".join(
            f'<li class="bu-pulse-{r.kind}">{html.escape(r.text)}</li>' for r in reminders
        )
        rem_html = f'<ul class="bu-pulse-list">{items}</ul>'
    else:
        rem_html = f'<p class="bu-pulse-muted">{html.escape(t("remind_none", lang))}</p>'

    cd_block = f'<p class="bu-pulse-cd">{html.escape(cd_detail or cd_label)}</p>'

    return f"""
<style>
.bu-pulse {{
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  margin: 0.25rem 0 0.85rem;
  padding: 0.85rem 0.9rem;
  border-radius: 16px;
  background: rgba(255,255,255,0.5);
  border: 1px solid rgba(255,255,255,0.7);
  box-shadow: 0 10px 24px rgba(31, 115, 140, 0.1);
  color: #1f4554;
  max-width: 100%;
  overflow-wrap: anywhere;
  word-break: break-word;
}}
.bu-pulse h4 {{
  margin: 0 0 0.35rem;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #3a7a8f;
  font-weight: 700;
}}
.bu-pulse + .bu-pulse, .bu-pulse .bu-pulse-sec {{ margin-top: 0.85rem; }}
.bu-pulse-sec {{ padding-top: 0.7rem; border-top: 1px solid rgba(31,115,140,0.12); }}
.bu-pulse-next {{
  margin: 0 0 0.45rem;
  font-weight: 700;
  font-size: 0.92rem;
  color: #176a82;
  line-height: 1.4;
}}
.bu-pulse-cd {{
  margin: 0;
  font-weight: 700;
  font-size: 0.95rem;
  line-height: 1.45;
  color: #1f4554;
}}
.bu-pulse-muted {{ margin: 0; font-size: 0.82rem; color: #5a7a88; line-height: 1.4; }}
.bu-pulse-gaps {{ margin: 0.4rem 0 0; font-size: 0.8rem; color: #3a7a8f; }}
.bu-pulse-list {{
  margin: 0.25rem 0 0;
  padding-left: 1.05rem;
  font-size: 0.8rem;
  line-height: 1.45;
}}
.bu-pulse-list.tight {{ font-size: 0.78rem; }}
.bu-pulse-rush {{ color: #b45a1a; }}
.bu-pulse-overlap {{ color: #a12d3a; font-weight: 650; }}
</style>
<div class="bu-pulse">
  <h4>{html.escape(t("pulse_today", lang))} · {html.escape(day_label)}</h4>
  {today_body}
  <div class="bu-pulse-sec">
    <h4>{html.escape(t("pulse_countdown", lang))}</h4>
    {cd_block}
  </div>
  <div class="bu-pulse-sec">
    <h4>{html.escape(t("pulse_tasks", lang))}</h4>
    {task_html}
  </div>
  <div class="bu-pulse-sec">
    <h4>{html.escape(t("pulse_remind", lang))}</h4>
    {rem_html}
  </div>
</div>
""".strip()


def pulse_context_for_llm(profile: StudentProfile, lang: Lang = "zh-CN") -> str:
    """Short block injected into the model context each turn."""
    now = datetime.now()
    status = clock_status(profile, now=now)
    day = weekday_code(now)
    lines = [
        "## 系统时钟（唯一权威 — 禁止猜测现在几点 / 是否下课）",
        f"- 现在: {now.strftime('%Y-%m-%d')} {day} {now.strftime('%H:%M')}（香港时间）",
        "- 浸大习惯：上课 xx:30，下课 xx:20；课间通常 10 分钟",
    ]

    if status.state == "no_tt":
        lines.append("- 状态: 尚未录入课表")
    elif status.state == "free_day":
        lines.append("- 状态: 今天没有课")
    elif status.state == "done":
        lines.append("- 状态: 今天课程已全部结束")
    elif status.state == "in_class" and status.slot is not None:
        s = status.slot
        left = status.minutes_to_end
        left_txt = f"还有 {left} 分钟下课" if left is not None else "尚未下课"
        lines.append(
            f"- 状态: **正在上课（未下课）** {s.course_code} {s.start_time}-{s.end_time} @ {s.location or 'TBA'}；{left_txt}"
        )
        lines.append(
            f"- 硬性: 禁止说「刚下课 / 已下课」；复习空档最早从 {status.free_from_hhmm} 开始"
        )
    elif status.state == "soon" and status.slot is not None:
        s = status.slot
        lines.append(
            f"- 状态: {status.minutes_to_start} 分钟后上课 {s.course_code} {s.start_time}-{s.end_time} @ {s.location or 'TBA'}"
        )
    elif status.state == "break" and status.slot is not None:
        s = status.slot
        lines.append(
            f"- 状态: 课间空档中；下一节 {s.course_code} {s.start_time}-{s.end_time}（还有 {status.minutes_to_start} 分钟）"
        )

    lines.append("")
    lines.append(f"## 今日课表（{day}）")
    slots = slots_on_day(profile, day)
    if not profile.timetable:
        lines.append("- 尚未录入课表")
    elif not slots:
        lines.append("- （无课）")
    else:
        now_m = now.hour * 60 + now.minute
        for s in slots:
            a, b = _to_minutes(s.start_time), _to_minutes(s.end_time)
            tag = ""
            if a is not None and b is not None:
                if a <= now_m < b:
                    tag = " ← 正在上"
                elif b <= now_m:
                    tag = " （已结束）"
                elif a > now_m:
                    tag = " （未开始）"
            lines.append(
                f"- {s.start_time}-{s.end_time} {s.course_code} @ {s.location or 'TBA'}{tag}"
            )

    lines.append("")
    lines.append("## 此刻起可用空档（已按系统时钟裁剪，排复习必须用这里）")
    week_gaps = remaining_week_gaps(profile, now=now, min_minutes=40)
    if week_gaps:
        for d, a, b in week_gaps[:14]:
            lines.append(f"- {d} {a}-{b}")
    else:
        lines.append("- （暂无足够长的空档）")

    _, detail = format_countdown(lang, today=now.date())
    if detail:
        lines.append("")
        lines.append(f"## 校历倒计时\n- {detail}")
    rems = detect_reminders(profile, lang=lang)[:4]
    if rems:
        lines.append("")
        lines.append("## 提醒")
        for r in rems:
            lines.append(f"- [{r.kind}] {r.text}")
    return "\n".join(lines)

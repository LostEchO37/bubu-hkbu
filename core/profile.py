"""Per-user profile: timetable, tasks, and imported email snippets."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import asdict, dataclass, field
from email import policy
from email.parser import BytesParser
from typing import Any


@dataclass
class CourseSlot:
    course_code: str
    course_name: str
    day: str
    start_time: str
    end_time: str
    location: str = ""


@dataclass
class TaskItem:
    title: str
    due: str = ""
    course: str = ""
    notes: str = ""
    source: str = "manual"


@dataclass
class EmailSnippet:
    subject: str
    sender: str
    date: str
    body_preview: str


@dataclass
class StudentProfile:
    name: str = ""
    student_id: str = ""
    programme: str = ""
    timetable: list[CourseSlot] = field(default_factory=list)
    tasks: list[TaskItem] = field(default_factory=list)
    emails: list[EmailSnippet] = field(default_factory=list)
    custom_notes: str = ""
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "student_id": self.student_id,
            "programme": self.programme,
            "timetable": [asdict(c) for c in self.timetable],
            "tasks": [asdict(t) for t in self.tasks],
            "emails": [asdict(e) for e in self.emails],
            "custom_notes": self.custom_notes,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StudentProfile:
        return cls(
            name=data.get("name", ""),
            student_id=data.get("student_id", ""),
            programme=data.get("programme", ""),
            timetable=[CourseSlot(**c) for c in data.get("timetable", [])],
            tasks=[TaskItem(**t) for t in data.get("tasks", [])],
            emails=[EmailSnippet(**e) for e in data.get("emails", [])],
            custom_notes=data.get("custom_notes", ""),
            settings=data.get("settings") or {},
        )


DAY_ALIASES = {
    "mon": "Mon",
    "monday": "Mon",
    "tue": "Tue",
    "tues": "Tue",
    "tuesday": "Tue",
    "wed": "Wed",
    "wednesday": "Wed",
    "thu": "Thu",
    "thur": "Thu",
    "thurs": "Thu",
    "thursday": "Thu",
    "fri": "Fri",
    "friday": "Fri",
    "sat": "Sat",
    "saturday": "Sat",
    "sun": "Sun",
    "sunday": "Sun",
    "一": "Mon",
    "周一": "Mon",
    "星期一": "Mon",
    "二": "Tue",
    "周二": "Tue",
    "星期二": "Tue",
    "三": "Wed",
    "周三": "Wed",
    "星期三": "Wed",
    "四": "Thu",
    "周四": "Thu",
    "星期四": "Thu",
    "五": "Fri",
    "周五": "Fri",
    "星期五": "Fri",
}


def normalize_day(raw: str) -> str:
    key = raw.strip().lower()
    return DAY_ALIASES.get(key, raw.strip()[:3].title() if raw.strip() else raw)


def parse_timetable_csv(text: str) -> list[CourseSlot]:
    """CSV columns: course_code,course_name,day,start_time,end_time,location"""
    reader = csv.DictReader(io.StringIO(text.strip()))
    slots: list[CourseSlot] = []
    for row in reader:
        if not any(row.values()):
            continue
        slots.append(
            CourseSlot(
                course_code=(row.get("course_code") or row.get("code") or "").strip(),
                course_name=(row.get("course_name") or row.get("name") or "").strip(),
                day=normalize_day(row.get("day") or ""),
                start_time=(row.get("start_time") or row.get("start") or "").strip(),
                end_time=(row.get("end_time") or row.get("end") or "").strip(),
                location=(row.get("location") or row.get("room") or "").strip(),
            )
        )
    return slots


def parse_timetable_freeform(text: str) -> list[CourseSlot]:
    """
    Lines like:
    COMP1234 Data Structures | Mon 09:30-11:00 | FSC801
    or: Mon 09:30-11:00 COMP1234 FSC801
    """
    slots: list[CourseSlot] = []
    time_pat = re.compile(
        r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun|周一|周二|周三|周四|周五)"
        r"\s+(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})",
        re.I,
    )
    code_pat = re.compile(r"\b([A-Z]{2,4}\d{4}[A-Z]?)\b")

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tm = time_pat.search(line)
        if not tm:
            continue
        day = normalize_day(tm.group(1))
        start, end = tm.group(2), tm.group(3)
        code_m = code_pat.search(line)
        code = code_m.group(1) if code_m else ""
        loc = ""
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                loc = parts[-1]
                name = parts[0]
            else:
                name = line
        else:
            name = line
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
    return slots


def parse_eml_bytes(data: bytes) -> EmailSnippet:
    msg = BytesParser(policy=policy.default).parsebytes(data)
    subject = str(msg.get("subject", ""))
    sender = str(msg.get("from", ""))
    date = str(msg.get("date", ""))
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content() or ""
                break
    else:
        body = msg.get_content() or ""
    preview = re.sub(r"\s+", " ", body).strip()[:1200]
    return EmailSnippet(subject=subject, sender=sender, date=date, body_preview=preview)


def extract_tasks_from_text(text: str, source: str = "import") -> list[TaskItem]:
    tasks: list[TaskItem] = []
    date_pat = re.compile(
        r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}|\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b)",
        re.I,
    )
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 4:
            continue
        if not re.search(r"assignment|homework|deadline|due|quiz|exam|project|报告|作业|截止", line, re.I):
            continue
        due_m = date_pat.search(line)
        tasks.append(TaskItem(title=line[:200], due=due_m.group(0) if due_m else "", source=source))
    return tasks


def _to_minutes(hhmm: str) -> int | None:
    try:
        h, m = hhmm.strip().split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return None


def _from_minutes(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"


def free_gaps(
    profile: StudentProfile,
    *,
    day_start: str = "08:30",
    day_end: str = "21:30",
    min_minutes: int = 45,
) -> list[tuple[str, str, str]]:
    """Infer study-friendly free windows from the weekly timetable."""
    start_m = _to_minutes(day_start)
    end_m = _to_minutes(day_end)
    if start_m is None or end_m is None:
        return []

    by_day: dict[str, list[CourseSlot]] = {}
    for slot in profile.timetable:
        by_day.setdefault(slot.day, []).append(slot)

    gaps: list[tuple[str, str, str]] = []
    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
        slots = sorted(by_day.get(day, []), key=lambda s: s.start_time)
        cursor = start_m
        for s in slots:
            s0 = _to_minutes(s.start_time)
            s1 = _to_minutes(s.end_time)
            if s0 is None or s1 is None:
                continue
            if s0 - cursor >= min_minutes:
                gaps.append((day, _from_minutes(cursor), _from_minutes(s0)))
            cursor = max(cursor, s1)
        if end_m - cursor >= min_minutes:
            gaps.append((day, _from_minutes(cursor), _from_minutes(end_m)))
    return gaps


def analyze_timetable(profile: StudentProfile) -> str:
    if not profile.timetable:
        return "尚未录入课表。请在侧边栏粘贴或上传课表，我才能分析你的上课时间与空闲时段。"

    by_day: dict[str, list[CourseSlot]] = {}
    for slot in profile.timetable:
        by_day.setdefault(slot.day, []).append(slot)

    lines = ["## 课表概览"]
    total_hours = 0.0
    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        if day not in by_day:
            continue
        lines.append(f"\n**{day}**")
        for s in sorted(by_day[day], key=lambda x: x.start_time):
            lines.append(
                f"- {s.start_time}–{s.end_time} {s.course_code} {s.course_name} @ {s.location or 'TBA'}"
            )
            try:
                sh, sm = map(int, s.start_time.split(":"))
                eh, em = map(int, s.end_time.split(":"))
                total_hours += (eh + em / 60) - (sh + sm / 60)
            except ValueError:
                pass

    codes = {s.course_code for s in profile.timetable if s.course_code}
    lines.append(f"\n共 **{len(profile.timetable)}** 个上课时段，约 **{total_hours:.1f}** 小时/周。")
    if codes:
        lines.append("课程代码：" + ", ".join(sorted(codes)) + "。")

    gaps = free_gaps(profile)
    if gaps:
        lines.append("\n**空档（≥45 分钟）**")
        for day, a, b in gaps[:12]:
            lines.append(f"- {day} {a}–{b}")
        if len(gaps) > 12:
            lines.append(f"- …另有 {len(gaps) - 12} 段")

    lines.append(
        "\n建议：把 assignment 截止日录入「任务」，我可以按课表空档帮你排自习与复习块。"
    )
    return "\n".join(lines)


def week_grid_html(profile: StudentProfile) -> str:
    """Compact visual week strip for the sidebar (pure HTML)."""
    if not profile.timetable:
        return ""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    by_day: dict[str, list[CourseSlot]] = {d: [] for d in days}
    for s in profile.timetable:
        if s.day in by_day:
            by_day[s.day].append(s)

    cols = []
    for day in days:
        slots = sorted(by_day[day], key=lambda x: x.start_time)
        cells = []
        for s in slots[:4]:
            label = html_escape(s.course_code or "·")
            tip = html_escape(f"{s.start_time}–{s.end_time} {s.course_code} @ {s.location or 'TBA'}")
            cells.append(f'<span class="bu-cell" title="{tip}">{label}</span>')
        if len(slots) > 4:
            cells.append(f'<span class="bu-cell more">+{len(slots) - 4}</span>')
        if not cells:
            cells.append('<span class="bu-cell empty">—</span>')
        cols.append(
            f'<div class="bu-col"><div class="bu-day">{day}</div>{"".join(cells)}</div>'
        )

    return f"""
<style>
.bu-week {{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0.35rem;
  margin: 0.35rem 0 0.75rem;
  font-family: "Noto Sans SC", sans-serif;
}}
.bu-col {{ display: flex; flex-direction: column; gap: 0.28rem; min-width: 0; }}
.bu-day {{
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #3a7a8f;
  text-align: center;
}}
.bu-cell {{
  display: block;
  font-size: 0.62rem;
  font-weight: 600;
  text-align: center;
  padding: 0.28rem 0.1rem;
  border-radius: 8px;
  background: linear-gradient(160deg, rgba(255,255,255,0.85), rgba(180,220,235,0.55));
  color: #1f4554;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border: 1px solid rgba(255,255,255,0.65);
}}
.bu-cell.empty {{ opacity: 0.35; background: rgba(255,255,255,0.25); }}
.bu-cell.more {{ opacity: 0.7; font-weight: 500; }}
</style>
<div class="bu-week">{"".join(cols)}</div>
""".strip()


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def mandatory_profile_context(
    profile: StudentProfile,
    display_name: str = "",
    account_username: str = "",
) -> str:
    """
    Full user snapshot injected on EVERY model call (not retrieval-based).
    """
    name = profile.name.strip() or display_name.strip() or "未留昵称"
    sid = profile.student_id.strip() or account_username.strip() or "未填学号"
    prog = profile.programme.strip() or "未填专业"

    lines = [
        "# 当前对话用户（系统每轮已加载 — 回答「我是谁/我的课表」必须只用此处信息）",
        f"- 称呼用: {name}",
        f"- 学号: {sid}",
        f"- 专业/课程: {prog}",
        "",
        "## 课表（完整）",
    ]
    if profile.timetable:
        lines.append(
            "状态: **已录入**（来自侧边栏识图，等价于用户已提供课表。"
            "禁止再要求上传或声称「没收到截图」。）"
        )
        for s in profile.timetable:
            lines.append(
                f"- {s.day} {s.start_time}-{s.end_time} | {s.course_code} {s.course_name} @ {s.location or 'TBA'}"
            )
        lines.append(f"（共 {len(profile.timetable)} 节课/周）")
        gaps = free_gaps(profile)
        lines.append("")
        lines.append("## 空档（推算，≥45 分钟，08:30–21:30）")
        if gaps:
            for day, a, b in gaps:
                lines.append(f"- {day} {a}-{b}")
        else:
            lines.append("（课表较满，几乎无长空档）")
    else:
        lines.append(
            "状态: **尚未录入** — 可提醒用户：左侧上传课表截图后点「AI 识别课表」。"
            "（聊天框本身不能收图。）"
        )

    lines.append("")
    lines.append("## 任务 / 截止日期")
    if profile.tasks:
        for t in profile.tasks[:40]:
            lines.append(f"- [{t.due or '无日期'}] {t.title} ({t.course or t.source})")
    else:
        lines.append("（暂无任务）")

    lines.append("")
    lines.append("## 邮件摘要")
    if profile.emails:
        for e in profile.emails[:8]:
            lines.append(f"- {e.subject} | {e.sender} | {e.date}")
            lines.append(f"  {e.body_preview[:500]}")
    else:
        lines.append("（无）")

    lines.append("")
    lines.append("## 用户备注")
    lines.append(profile.custom_notes.strip() if profile.custom_notes.strip() else "（无）")

    return "\n".join(lines)


def profile_context_for_llm(profile: StudentProfile) -> str:
    """Backward-compatible alias."""
    return mandatory_profile_context(profile)


def dumps_profile(profile: StudentProfile) -> str:
    return json.dumps(profile.to_dict(), ensure_ascii=False, indent=2)


def loads_profile(raw: str) -> StudentProfile:
    return StudentProfile.from_dict(json.loads(raw))

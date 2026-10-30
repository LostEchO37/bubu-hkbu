#!/usr/bin/env python3
"""Unit checks for timetable vision JSON repair (no API)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.timetable_vision import _parse_courses_payload, _slots_from_courses  # noqa: E402


def main() -> None:
    truncated = (
        '{"courses":[{"course_code":"GFQR1026","course_name":"","day":"Tue",'
        '"start_time":"09:30","end_time":"10:30","location":"OEE1017"},'
        '{"course_code":"ECON3076","course_name":"","day":"Tue",'
        '"start_time":"12:30","end_time":"15:30","location":"WLB204"},'
        '{"course_code":"GTSC2066","course_name":"","day":"Wed",'
        '"start_time":"14:30","end_time":"16:30","location":"FSC801C'
    )
    courses = _parse_courses_payload(truncated)
    assert len(courses) >= 2, courses
    slots = _slots_from_courses(courses)
    assert any(s.course_code == "GFQR1026" and s.day == "Tue" for s in slots)

    fenced = '```json\n{"courses":[{"course_code":"X","day":"Fri","start_time":"15:30","end_time":"18:30","location":"DLB303"}]}\n```'
    assert _parse_courses_payload(fenced)[0]["course_code"] == "X"

    print("test_timetable_json_repair: ok")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate GTSC2066 group project build guide PDF from Markdown."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "docs" / "GTSC2066_Group_Project_Build_Guide.md"
OUT_PATH = ROOT / "docs" / "GTSC2066_Group_Project_Build_Guide.pdf"

FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]


def find_font() -> str:
    for p in FONT_CANDIDATES:
        if Path(p).is_file():
            return p
    return ""


def md_to_lines(text: str) -> list[tuple[str, str]]:
    """Return list of (style, line) where style in title, h2, h3, body, bullet."""
    out: list[tuple[str, str]] = []
    in_code = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            out.append(("code", line))
            continue
        if not line.strip():
            out.append(("blank", ""))
            continue
        if line.startswith("# "):
            out.append(("title", line[2:].strip()))
        elif line.startswith("## "):
            out.append(("h2", line[3:].strip()))
        elif line.startswith("### "):
            out.append(("h3", line[4:].strip()))
        elif line.startswith("- "):
            out.append(("bullet", line[2:].strip()))
        else:
            out.append(("body", line))
    return out


def sanitize(s: str) -> str:
    # Remove emoji / rare symbols that break some TTC fonts in fpdf2
    return re.sub(
        r"[^\u0020-\u007e\u00a0-\u9fff\u3000-\u303f\uff00-\uffef，。、；：？！（）《》【】""''·—]",
        "",
        s,
    )


def wrap_long(s: str, max_len: int = 90) -> list[str]:
    s = sanitize(s.replace("\t", " "))
    if len(s) <= max_len:
        return [s]
    parts: list[str] = []
    while len(s) > max_len:
        cut = s.rfind(" ", 0, max_len)
        if cut < 20:
            cut = max_len
        parts.append(s[:cut])
        s = s[cut:].lstrip()
    if s:
        parts.append(s)
    return parts


def main() -> int:
    try:
        from fpdf import FPDF
    except ImportError:
        print("Install fpdf2: pip install fpdf2", file=sys.stderr)
        return 1

    if not MD_PATH.is_file():
        print(f"Missing {MD_PATH}", file=sys.stderr)
        return 1

    font_path = find_font()
    if not font_path:
        print("No Unicode font found for Chinese PDF.", file=sys.stderr)
        return 1

    text = MD_PATH.read_text(encoding="utf-8")
    lines = md_to_lines(text)

    pdf = FPDF()
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.add_font("CJK", "", font_path)
    pdf.set_font("CJK", size=10)

    epw = pdf.epw

    def write_lines(style: str, content: str) -> None:
        content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)
        content = content.replace("`", "")
        for piece in wrap_long(content):
            if not piece.strip():
                continue
            try:
                if style == "title":
                    pdf.set_font("CJK", size=15)
                    pdf.multi_cell(epw, 9, piece)
                    pdf.set_font("CJK", size=10)
                elif style == "h2":
                    pdf.set_font("CJK", size=12)
                    pdf.multi_cell(epw, 7, piece)
                    pdf.set_font("CJK", size=10)
                elif style == "h3":
                    pdf.set_font("CJK", size=11)
                    pdf.multi_cell(epw, 6, piece)
                    pdf.set_font("CJK", size=10)
                elif style == "bullet":
                    pdf.multi_cell(epw, 5, "- " + piece)
                elif style == "code":
                    pdf.set_font("CJK", size=9)
                    pdf.multi_cell(epw, 5, "  " + piece)
                    pdf.set_font("CJK", size=10)
                else:
                    pdf.multi_cell(epw, 5, piece)
            except Exception:
                pdf.multi_cell(epw, 5, piece.encode("ascii", "ignore").decode())

    for style, line in lines:
        if style == "blank":
            pdf.ln(3)
            continue
        if style == "h2":
            pdf.ln(2)
        write_lines(style, line)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_PATH))
    print(f"Wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Keyword retrieval + query expansion for HKBU knowledge files."""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"

# Chinese/English query expansion (not ML — improves recall for mixed KB)
QUERY_EXPANSIONS: dict[str, list[str]] = {
    "考试": ["examination", "examinations", "exam", "考试周", "期末", "测验"],
    "考试周": ["examination", "examinations", "exam period", "first semester examinations", "second semester"],
    "校历": ["academic calendar", "calendar", "2026", "2027", "semester", "学年", "学期"],
    "学期": ["semester", "first semester", "second semester", "trimester"],
    "counselling": ["辅导", "心理咨询", "3411 7435", "cdc"],
    "辅导": ["counselling", "cdc", "3411 7435"],
    "实验室": ["lab", "laboratory", "FSC801", "opening hours", "computer"],
    "课表": ["timetable", "class", "course"],
}

PINNED_FOR_CALENDAR = [
    "academic_calendar_2026_27_zh.md",
    "academic_calendar_2026_27.md",
]


@dataclass
class Chunk:
    source: str
    text: str
    score: float


def _tokenize(text: str) -> set[str]:
    tokens = {t for t in re.findall(r"[a-z0-9\u4e00-\u9fff]+", text.lower()) if len(t) > 1}
    han = re.findall(r"[\u4e00-\u9fff]+", text)
    for seg in han:
        for i in range(len(seg) - 1):
            tokens.add(seg[i : i + 2])
    return tokens


def _expand_query(query: str) -> set[str]:
    tokens = _tokenize(query)
    q_lower = query.lower()
    for key, extras in QUERY_EXPANSIONS.items():
        if key in q_lower or key in query:
            tokens.update(_tokenize(" ".join(extras)))
    return tokens


def _load_documents() -> list[tuple[str, str]]:
    docs: list[tuple[str, str]] = []
    if not KNOWLEDGE_DIR.is_dir():
        return docs
    for path in sorted(KNOWLEDGE_DIR.iterdir()):
        if path.suffix.lower() in {".md", ".txt"}:
            docs.append((path.name, path.read_text(encoding="utf-8", errors="replace")))
    return docs


def _load_file(name: str) -> str | None:
    path = KNOWLEDGE_DIR / name
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace")
    return None


def _split_chunks(text: str, max_len: int = 900) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for p in paragraphs:
        if size + len(p) > max_len and buf:
            chunks.append("\n\n".join(buf))
            buf, size = [], 0
        buf.append(p)
        size += len(p)
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


@functools.lru_cache(maxsize=1)
def _indexed_chunks() -> tuple[tuple[str, str, frozenset[str]], ...]:
    """Pre-tokenize knowledge once — hot path on every chat turn."""
    rows: list[tuple[str, str, frozenset[str]]] = []
    for source, body in _load_documents():
        for piece in _split_chunks(body):
            tokens = _tokenize(piece)
            if tokens:
                rows.append((source, piece, frozenset(tokens)))
    return tuple(rows)


@functools.lru_cache(maxsize=8)
def _cached_file(name: str) -> str | None:
    return _load_file(name)


def _is_calendar_query(query: str) -> bool:
    keys = ("校历", "考试", "学期", "calendar", "exam", "semester", "add/drop", "选课")
    q = query.lower()
    return any(k in query or k in q for k in keys)


def search_knowledge(query: str, top_k: int = 6) -> list[Chunk]:
    q_tokens = _expand_query(query)
    if not q_tokens:
        return []

    scored: list[Chunk] = []
    seen: set[tuple[str, str]] = set()
    for source, piece, tokens in _indexed_chunks():
        overlap = len(q_tokens & tokens)
        if overlap <= 0:
            continue
        score = overlap / (len(q_tokens) ** 0.5)
        key = (source, piece[:80])
        if key not in seen:
            seen.add(key)
            scored.append(Chunk(source=source, text=piece, score=score))

    scored.sort(key=lambda c: c.score, reverse=True)
    chunks = scored[:top_k]

    if _is_calendar_query(query):
        pinned: list[Chunk] = []
        for name in PINNED_FOR_CALENDAR:
            body = _cached_file(name)
            if body:
                pinned.append(Chunk(source=name, text=body[:3500], score=999.0))
        existing = {c.source for c in pinned}
        chunks = pinned + [c for c in chunks if c.source not in existing]
        chunks = chunks[: max(top_k, len(pinned))]

    return chunks


@functools.lru_cache(maxsize=1)
def mandatory_bootstrap() -> str:
    """Always send current-year calendar + campus FAQ (small files)."""
    parts: list[str] = []
    for name in (
        "academic_calendar_2026_27_zh.md",
        "hkbu_campus_faq_zh.md",
    ):
        body = _cached_file(name)
        if body:
            parts.append(f"### {name}\n{body}")
    return "\n\n".join(parts)


def format_knowledge_context(chunks: list[Chunk]) -> str:
    if not chunks:
        return ""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[{i}] ({c.source})\n{c.text}")
    return "\n\n---\n\n".join(parts)

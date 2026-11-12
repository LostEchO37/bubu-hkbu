"""Retrieval-augmented generation over HKBU knowledge files (BM25-lite + expansions)."""

from __future__ import annotations

import functools
import math
import re
from dataclasses import dataclass, field
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
    "天气": ["weather", "气温", "降雨", "台风", "天文台", "hko", "humidity", "warning"],
    "下雨": ["rain", "rainfall", "暴雨", "weather", "天文台"],
    "台风": ["tropical cyclone", "typhoon", "警告", "天文台", "weather"],
    "放假": ["holiday", "public holiday", "校历", "calendar"],
}

PINNED_FOR_CALENDAR = [
    "academic_calendar_2026_27_zh.md",
    "academic_calendar_2026_27.md",
]

_WEATHER_KEYS = (
    "天气",
    "气温",
    "下雨",
    "降雨",
    "台风",
    "暴雨",
    "酷热",
    "寒冷",
    "湿度",
    "天文台",
    "weather",
    "rain",
    "typhoon",
    "hko",
    "forecast",
    "warning",
    "umbrella",
)


@dataclass
class Chunk:
    source: str
    text: str
    score: float


@dataclass
class RetrievalBundle:
    """One RAG turn: ranked chunks + optional live facts + citation labels."""

    chunks: list[Chunk] = field(default_factory=list)
    live_facts: str = ""
    citations: list[str] = field(default_factory=list)
    include_live_weather: bool = False


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


@functools.lru_cache(maxsize=1)
def _idf_table() -> dict[str, float]:
    """Document-frequency IDF over knowledge chunks (BM25-lite)."""
    rows = _indexed_chunks()
    n = max(len(rows), 1)
    df: dict[str, int] = {}
    for _src, _text, tokens in rows:
        for tok in tokens:
            df[tok] = df.get(tok, 0) + 1
    return {tok: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5)) for tok, freq in df.items()}


@functools.lru_cache(maxsize=8)
def _cached_file(name: str) -> str | None:
    return _load_file(name)


def _is_calendar_query(query: str) -> bool:
    keys = ("校历", "考试", "学期", "calendar", "exam", "semester", "add/drop", "选课")
    q = query.lower()
    return any(k in query or k in q for k in keys)


def is_weather_query(query: str) -> bool:
    q = query.lower()
    return any(k in query or k in q for k in _WEATHER_KEYS)


def _bm25_score(q_tokens: set[str], doc_tokens: frozenset[str], *, avgdl: float) -> float:
    """BM25-lite without term frequency counts beyond presence (sparse FAQ chunks)."""
    if not q_tokens or not doc_tokens:
        return 0.0
    idf = _idf_table()
    dl = max(len(doc_tokens), 1)
    k1, b = 1.4, 0.75
    score = 0.0
    for tok in q_tokens:
        if tok not in doc_tokens:
            continue
        # binary tf=1 for short FAQ chunks
        tf = 1.0
        idf_w = idf.get(tok, 1.2)
        denom = tf + k1 * (1.0 - b + b * dl / max(avgdl, 1.0))
        score += idf_w * (tf * (k1 + 1.0) / denom)
    # Prefer denser overlap
    overlap = len(q_tokens & doc_tokens)
    score += 0.15 * overlap
    return score


def search_knowledge(query: str, top_k: int = 6) -> list[Chunk]:
    q_tokens = _expand_query(query)
    if not q_tokens:
        return []

    rows = _indexed_chunks()
    avgdl = sum(len(toks) for _s, _t, toks in rows) / max(len(rows), 1)
    scored: list[Chunk] = []
    seen: set[tuple[str, str]] = set()
    for source, piece, tokens in rows:
        score = _bm25_score(q_tokens, tokens, avgdl=avgdl)
        if score <= 0:
            continue
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


def retrieve(query: str, *, top_k: int = 6, lang: str = "zh-CN") -> RetrievalBundle:
    """Full RAG step: KB search + live HKO facts when relevant (or lightly always)."""
    chunks = search_knowledge(query, top_k=top_k)
    want_weather = is_weather_query(query)
    live = ""
    try:
        from core.live_facts import live_facts_for_llm

        live = live_facts_for_llm(lang)  # type: ignore[arg-type]
    except Exception:
        live = "## 实时天气\n- （暂不可用）"
    citations = [c.source for c in chunks]
    seen: set[str] = set()
    uniq: list[str] = []
    for name in citations:
        if name not in seen:
            seen.add(name)
            uniq.append(name)
    if want_weather or live:
        uniq.append("Hong Kong Observatory (live)")
    return RetrievalBundle(
        chunks=chunks,
        live_facts=live,
        citations=uniq,
        include_live_weather=bool(live),
    )


@functools.lru_cache(maxsize=1)
def mandatory_bootstrap() -> str:
    """Always send current-year calendar + campus FAQ (small files)."""
    parts: list[str] = []
    for name in (
        "academic_calendar_2026_27_zh.md",
        "hkbu_campus_faq_zh.md",
        "official_links_zh.md",
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
        parts.append(f"[{i}] ({c.source}, score={c.score:.2f})\n{c.text}")
    return "\n\n---\n\n".join(parts)


def format_retrieval_block(bundle: RetrievalBundle) -> str:
    kb = format_knowledge_context(bundle.chunks)
    parts = [
        "## 检索补充（RAG）",
        kb or "（无额外知识库片段）",
        "",
        bundle.live_facts or "",
    ]
    if bundle.citations:
        parts.append("")
        parts.append("## 本轮依据来源")
        for name in bundle.citations[:8]:
            parts.append(f"- {name}")
    return "\n".join(parts)

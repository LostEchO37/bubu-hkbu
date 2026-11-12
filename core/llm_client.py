"""Shared OpenAI-compatible client (no RAG / vision imports — avoids circular deps)."""

from __future__ import annotations

import functools
import os

from openai import OpenAI


@functools.lru_cache(maxsize=8)
def _client_cached(api_key: str, base_url: str, provider: str, model_set: str) -> OpenAI:
    del model_set  # part of cache key so missing-model fails fast when env changes
    timeout = float(os.environ.get("OPENAI_TIMEOUT", "90"))
    kwargs = {"api_key": api_key, "timeout": timeout}
    if provider in {"hkbu", "hkbu_genai", "genai"}:
        return OpenAI(base_url=base_url or "https://genai.hkbu.edu.hk/api/v1", **kwargs)
    return OpenAI(base_url=base_url or None, **kwargs)


def get_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("请设置环境变量 OPENAI_API_KEY。")

    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
    model = os.environ.get("OPENAI_MODEL", "").strip()

    if provider in {"hkbu", "hkbu_genai", "genai"} and not model:
        raise RuntimeError("缺少 OPENAI_MODEL 环境变量。")

    return _client_cached(api_key, base_url, provider, model)


# Back-compat alias used by vision modules
_client = get_openai_client

"""OpenAI-compatible chat with retrieval-augmented HKBU context."""

from __future__ import annotations

import functools
import os

from openai import OpenAI

from core.app_settings import Personality, temperature_for
from core.i18n import LLM_LANG_HINT, Lang
from core.knowledge import format_knowledge_context, mandatory_bootstrap, search_knowledge
from core.persona import get_persona
from core.profile import StudentProfile, mandatory_profile_context
from core.today import pulse_context_for_llm

SYSTEM_PROMPT = """你是「阿Bu」（英文可称 BuBu）——浸大同学助手，学长/学姐型 AI 搭档（见下方人设）。

能力：
1. 用已加载的浸大资料 + 用户个人资料（课表、任务、今日快览）回答问题、做规划。
2. 校历、校园服务、CS 设施等以「浸大固定资料」为准。

硬性规则：
- **每轮对话都已注入「当前对话用户」完整资料**；用户问身份、课表、任务时必须直接引用，禁止说「我不知道你是谁 / 没加载课表」。
- **课表来自左侧栏「AI 识别课表」**，不是聊天框附件。若注入资料里「课表（完整）」已有条目：视为已录入，禁止说「还没收到截图 / 请去上传」；应直接用课表回答空档、冲突、复习安排。只有资料写「尚未上传」时才可催上传。
- **「系统时钟」是唯一权威**：里面的「现在 / 正在上课 / 还有 X 分钟下课」必须照抄。若写着「正在上课（未下课）」，禁止说「刚下课 / 已下课 / 下完了」。
- **排复习只准用「此刻起可用空档」列表**（已按当前时间裁剪）。不要把还没结束的课算进空档；下课前最早只能从 `free_from` 开始排。
- **浸大时间习惯**：上课 xx:30，下课 xx:20，课间通常 10 分钟。
- **赶场/冲突提醒**若已列出，回答规划时要主动避开或提醒。
- **浸大 2026–27 校历已在固定资料中**；有考试周日期就必须直说，禁止声称没有校历。
- 对话历史里若曾有错误回答（例如明明有课表却说没有、时间说错），以本轮 injected 资料为准并纠正。
- 不编造日期、政策、费用；危机/心理/安全话题立刻严肃，给 counselling 3411 7435。
- 规划学习时给可执行时间块，结合课表空档；回答尽量短而落地（先结论，再要点）。
"""


def get_openai_client() -> OpenAI:
    return _client()


@functools.lru_cache(maxsize=8)
def _client_cached(api_key: str, base_url: str, provider: str, model_set: str) -> OpenAI:
    del model_set  # part of cache key so missing-model fails fast when env changes
    if provider in {"hkbu", "hkbu_genai", "genai"}:
        return OpenAI(api_key=api_key, base_url=base_url or "https://genai.hkbu.edu.hk/api/v1")
    return OpenAI(api_key=api_key, base_url=base_url or None)


def _client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("请设置环境变量 OPENAI_API_KEY。")

    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
    model = os.environ.get("OPENAI_MODEL", "").strip()

    if provider in {"hkbu", "hkbu_genai", "genai"} and not model:
        raise RuntimeError("缺少 OPENAI_MODEL 环境变量。")

    return _client_cached(api_key, base_url, provider, model)


def build_messages(
    user_message: str,
    history: list[dict[str, str]],
    profile: StudentProfile,
    lang: Lang = "zh-CN",
    display_name: str = "",
    account_username: str = "",
    personality: Personality = "playful",
) -> list[dict[str, str]]:
    chunks = search_knowledge(user_message, top_k=6)
    kb = format_knowledge_context(chunks)
    user_block = mandatory_profile_context(profile, display_name, account_username)
    pulse = pulse_context_for_llm(profile, lang)
    bootstrap = mandatory_bootstrap()

    context_block = f"""{user_block}

{pulse}

---

## 浸大固定资料（每轮必载）
{bootstrap}

## 检索补充（按问题）
{kb or "（无额外片段）"}
"""
    lang_hint = LLM_LANG_HINT.get(lang, LLM_LANG_HINT["zh-CN"])
    persona = get_persona(lang, personality)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{persona}\n\n{lang_hint}"}
    ]
    messages.append({"role": "system", "content": context_block})
    # Keep recent turns; drop oversized blobs so latency stays tight.
    for turn in history[-10:]:
        content = turn["content"]
        if len(content) > 4000:
            content = content[:3800] + "…"
        messages.append({"role": turn["role"], "content": content})
    messages.append({"role": "user", "content": user_message})
    return messages


def chat_completion(
    user_message: str,
    history: list[dict[str, str]],
    profile: StudentProfile,
    model: str | None = None,
    lang: Lang = "zh-CN",
    display_name: str = "",
    account_username: str = "",
    personality: Personality = "playful",
) -> str:
    client = _client()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    messages = build_messages(
        user_message, history, profile, lang=lang,
        display_name=display_name, account_username=account_username,
        personality=personality,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature_for(personality),
    )
    return (resp.choices[0].message.content or "").strip()


def chat_completion_stream(
    user_message: str,
    history: list[dict[str, str]],
    profile: StudentProfile,
    model: str | None = None,
    lang: Lang = "zh-CN",
    display_name: str = "",
    account_username: str = "",
    personality: Personality = "playful",
):
    client = _client()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    messages = build_messages(
        user_message, history, profile, lang=lang,
        display_name=display_name, account_username=account_username,
        personality=personality,
    )
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature_for(personality),
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def suggest_study_plan(
    profile: StudentProfile,
    focus: str = "",
    lang: Lang = "zh-CN",
    display_name: str = "",
    account_username: str = "",
    personality: Personality = "playful",
) -> str:
    prompts = {
        "zh-CN": "根据「当前对话用户」里的课表和任务，生成本周学习计划（按天+时间块）。语气像同学，但安排要靠谱。",
        "zh-TW": "根據「當前對話用戶」裏的課表和任務，生成本週學習計劃（按日+時間塊）。語氣像同學，但安排要靠谱。",
        "en": "From the loaded timetable and tasks, create this week's study plan. Buddy tone, solid schedule.",
    }
    prompt = prompts.get(lang, prompts["zh-CN"])
    if focus.strip():
        prompt += f"\n{focus.strip()}"
    return chat_completion(
        prompt, [], profile, lang=lang,
        display_name=display_name, account_username=account_username,
        personality=personality,
    )

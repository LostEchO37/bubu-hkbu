"""In-app release notes (shown in sidebar)."""

from __future__ import annotations

from core.i18n import Lang

# Newest first. Keep short — students skim, they don't read novels.
ENTRIES: list[dict[str, dict[Lang, str] | str]] = [
    {
        "date": "2026-11-04",
        "title": {
            "zh-CN": "界面与稳定性",
            "zh-TW": "介面與穩定性",
            "en": "UI & stability",
        },
        "body": {
            "zh-CN": "· 深色模式按钮/标题可读性\n· 设置改为开关，不再一点就关\n· 我的资料改为聊天下方独立折叠\n· 语言/语气需点「应用设置」生效\n· 修复主题 CSS 整页刷成代码的问题",
            "zh-TW": "· 深色模式按鈕/標題可讀性\n· 設定改為開關，不再一點就關\n· 我的資料改為聊天下方獨立摺疊\n· 語言/語氣需點「套用設定」生效\n· 修復主題 CSS 整頁刷成程式碼的問題",
            "en": "· Dark-mode button/header contrast\n· Settings use a sticky toggle\n· Workspace is one expander under chat\n· Language/tone apply only on Apply\n· Fixed theme CSS dumping as page text",
        },
    },
    {
        "date": "2026-11-03",
        "title": {
            "zh-CN": "Cloud 演示上线",
            "zh-TW": "Cloud 示範上線",
            "en": "Cloud demo live",
        },
        "body": {
            "zh-CN": "· Streamlit Cloud 公开访问\n· 气泡导航保持登录\n· Cloud 数据可能休眠清空的提示",
            "zh-TW": "· Streamlit Cloud 公開訪問\n· 氣泡導航保持登入\n· Cloud 資料可能休眠清空的提示",
            "en": "· Public Streamlit Cloud deploy\n· Bubble links keep you signed in\n· Notice that Cloud storage can wipe on sleep",
        },
    },
]


def changelog_markdown(lang: Lang) -> str:
    lines: list[str] = []
    for entry in ENTRIES:
        date = str(entry["date"])
        title_map = entry["title"]
        body_map = entry["body"]
        assert isinstance(title_map, dict) and isinstance(body_map, dict)
        title = title_map.get(lang) or title_map.get("zh-CN") or ""
        body = body_map.get(lang) or body_map.get("zh-CN") or ""
        lines.append(f"**{date} · {title}**")
        lines.append(body)
        lines.append("")
    return "\n".join(lines).strip()

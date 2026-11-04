"""In-app release notes — product-facing only, no private paths/secrets/accounts."""

from __future__ import annotations

from core.i18n import Lang

# Newest first. One entry per public push; wording avoids private ops details.
ENTRIES: list[dict[str, dict[Lang, str] | str]] = [
    {
        "date": "2026-11-04",
        "tag": "v0.14",
        "title": {
            "zh-CN": "更新日志入口 + 标题字体",
            "zh-TW": "更新日誌入口 + 標題字體",
            "en": "Changelog + hub typeface",
        },
        "body": {
            "zh-CN": "· 新增应用内更新日志\n· 首页大标题字体改为更舒展的 Outfit，不再显得扁",
            "zh-TW": "· 新增應用內更新日誌\n· 首頁大標題字體改為更舒展的 Outfit，不再顯得扁",
            "en": "· In-app changelog\n· Hub title uses Outfit so it no longer looks squashed",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.13",
        "title": {
            "zh-CN": "主题样式泄漏修复",
            "zh-TW": "主題樣式洩漏修復",
            "en": "Theme CSS leak fix",
        },
        "body": {
            "zh-CN": "· 修复主题 CSS 被当成正文显示在页面上的问题\n· 样式改回安全注入方式，主界面恢复正常",
            "zh-TW": "· 修復主題 CSS 被當成正文顯示在頁面上的問題\n· 樣式改回安全注入方式，主介面恢復正常",
            "en": "· Fixed theme CSS rendering as visible page text\n· Restored safe style injection so the UI looks normal again",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.12",
        "title": {
            "zh-CN": "设置稳定 + 资料区折叠",
            "zh-TW": "設定穩定 + 資料區摺疊",
            "en": "Sticky settings + workspace expander",
        },
        "body": {
            "zh-CN": "· 设置改为开关，打开后不会一点就关\n· 「我的资料」改为聊天下方独立折叠，避免双栏刷新卡格式\n· 继续加强深色模式按钮/折叠标题对比度",
            "zh-TW": "· 設定改為開關，打開後不會一點就關\n· 「我的資料」改為聊天下方獨立摺疊，避免雙欄刷新卡格式\n· 繼續加強深色模式按鈕/摺疊標題對比度",
            "en": "· Settings use a sticky toggle (no snap-shut)\n· Workspace is one expander under chat (avoids column reflow)\n· Stronger dark-mode contrast on buttons/headers",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.11",
        "title": {
            "zh-CN": "深色模式对比度（控件）",
            "zh-TW": "深色模式對比度（控件）",
            "en": "Dark-mode control contrast",
        },
        "body": {
            "zh-CN": "· 修复深色下按钮、折叠栏、上传区文字发白看不见\n· 统一主区与侧栏控件配色",
            "zh-TW": "· 修復深色下按鈕、摺疊欄、上傳區文字發白看不見\n· 統一主區與側欄控件配色",
            "en": "· Fixed washed-out button/expander/uploader text in dark mode\n· Unified control colors in main area and sidebar",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.10",
        "title": {
            "zh-CN": "应用设置报错 + 布局调整",
            "zh-TW": "套用設定報錯 + 版面調整",
            "en": "Apply-settings crash + layout",
        },
        "body": {
            "zh-CN": "· 修复点「应用设置」先报错再切换的问题\n· 左侧精简为今天概览/设置；资料、课表、邮件移到右侧工作区",
            "zh-TW": "· 修復點「套用設定」先報錯再切換的問題\n· 左側精簡為今天概覽/設定；資料、課表、郵件移到右側工作區",
            "en": "· Fixed Apply settings error-then-switch glitch\n· Slim left rail (Today/settings); profile tools moved to workspace",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.9",
        "title": {
            "zh-CN": "语气与备注反馈",
            "zh-TW": "語氣與備註回饋",
            "en": "Tone + notes feedback",
        },
        "body": {
            "zh-CN": "· 强化助手语气提示，应用后侧栏显示当前语气\n· 「更多备注」留在折叠内，可保存并提示会用于对话\n· 去掉侧栏脉冲卡片上的多余角标遮挡",
            "zh-TW": "· 強化助手語氣提示，套用後側欄顯示當前語氣\n· 「更多備註」留在摺疊內，可保存並提示會用於對話\n· 去掉側欄脈衝卡片上的多餘角標遮擋",
            "en": "· Stronger tone prompts; active tone shown after Apply\n· Notes stay inside More, with save confirmation for chat use\n· Removed stray badge overlay on the Today pulse card",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.8",
        "title": {
            "zh-CN": "设置语言不再中英混杂",
            "zh-TW": "設定語言不再中英混雜",
            "en": "No mixed-language settings labels",
        },
        "body": {
            "zh-CN": "· 切换界面语言并应用后，字号/语气选项跟当前语言一致\n· 按语言隔离设置控件，避免残留上次语言的英文标签",
            "zh-TW": "· 切換介面語言並套用後，字級/語氣選項跟當前語言一致\n· 按語言隔離設定控件，避免殘留上次語言的英文標籤",
            "en": "· Font/tone labels match the applied UI language\n· Per-language setting widgets avoid leftover English labels",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.7",
        "title": {
            "zh-CN": "设置需确认才生效",
            "zh-TW": "設定需確認才生效",
            "en": "Settings apply on confirm only",
        },
        "body": {
            "zh-CN": "· 语言/字号/外观/语气改为草稿，需点「应用设置」\n· 修复应用时误改已创建控件导致的崩溃",
            "zh-TW": "· 語言/字級/外觀/語氣改為草稿，需點「套用設定」\n· 修復套用時誤改已建立控件導致的崩潰",
            "en": "· Language/font/theme/tone are drafts until Apply\n· Fixed crash from mutating widget keys after create",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.6",
        "title": {
            "zh-CN": "浅色默认与对话超时",
            "zh-TW": "淺色預設與對話超時",
            "en": "Light default + chat timeout",
        },
        "body": {
            "zh-CN": "· 外观默认浅色；空选不再被当成深色\n· 模型请求加超时，减少对话一直卡住\n· 继续修补深色模式可读性",
            "zh-TW": "· 外觀預設淺色；空選不再被當成深色\n· 模型請求加超時，減少對話一直卡住\n· 繼續修補深色模式可讀性",
            "en": "· Appearance defaults to light; empty radio no longer becomes dark\n· Model calls time out instead of hanging the chat\n· More dark-mode readability fixes",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.5",
        "title": {
            "zh-CN": "语言跨页面保持",
            "zh-TW": "語言跨頁面保持",
            "en": "Language persists across views",
        },
        "body": {
            "zh-CN": "· 气泡跳转时界面与助手语言不再掉回简体\n· 登录侧栏提示可在此切换语言\n· 语言写入链接参数与账号设置",
            "zh-TW": "· 氣泡跳轉時介面與助手語言不再掉回簡體\n· 登入側欄提示可在此切換語言\n· 語言寫入連結參數與帳號設定",
            "en": "· UI + chatbot language no longer resets on bubble navigation\n· Login sidebar tip for changing language\n· Language kept in URL and account settings",
        },
    },
    {
        "date": "2026-11-03",
        "tag": "v0.4",
        "title": {
            "zh-CN": "Cloud 依赖兼容",
            "zh-TW": "Cloud 依賴相容",
            "en": "Cloud dependency compatibility",
        },
        "body": {
            "zh-CN": "· 放宽 Streamlit 版本限制，便于云端安装依赖",
            "zh-TW": "· 放寬 Streamlit 版本限制，便於雲端安裝依賴",
            "en": "· Relaxed Streamlit pin so Cloud can resolve packages",
        },
    },
    {
        "date": "2026-11-03",
        "tag": "v0.3",
        "title": {
            "zh-CN": "Cloud 体验与说明",
            "zh-TW": "Cloud 體驗與說明",
            "en": "Cloud UX honesty",
        },
        "body": {
            "zh-CN": "· 明确提示演示环境重启/休眠可能清空数据\n· 完善部署说明与视觉自检",
            "zh-TW": "· 明確提示示範環境重啟/休眠可能清空資料\n· 完善部署說明與視覺自檢",
            "en": "· Clear notice that demo reboot/sleep may wipe data\n· Deploy docs and visual self-check improvements",
        },
    },
    {
        "date": "2026-11-03",
        "tag": "v0.2",
        "title": {
            "zh-CN": "云端部署准备",
            "zh-TW": "雲端部署準備",
            "en": "Cloud deploy prep",
        },
        "body": {
            "zh-CN": "· 运行环境与会话安全配置接线\n· 支持公开演示部署",
            "zh-TW": "· 運行環境與會話安全配置接線\n· 支援公開示範部署",
            "en": "· Runtime and session security wiring\n· Ready for public demo hosting",
        },
    },
    {
        "date": "2026-11-02",
        "tag": "v0.1",
        "title": {
            "zh-CN": "首发：阿Bu 同学助手",
            "zh-TW": "首發：阿Bu 同學助手",
            "en": "First release: BuBu campus buddy",
        },
        "body": {
            "zh-CN": "· 登录注册与多语言界面\n· 课表识别、任务、邮件草稿\n· 气泡主页与悬浮球浏览器插件",
            "zh-TW": "· 登入註冊與多語言介面\n· 課表識別、任務、郵件草稿\n· 氣泡主頁與懸浮球瀏覽器外掛",
            "en": "· Sign-in and multilingual UI\n· Timetable scan, tasks, email drafts\n· Bubble hub and floating-orb browser extension",
        },
    },
]


def changelog_markdown(lang: Lang) -> str:
    lines: list[str] = []
    for entry in ENTRIES:
        date = str(entry["date"])
        tag = str(entry.get("tag", ""))
        title_map = entry["title"]
        body_map = entry["body"]
        assert isinstance(title_map, dict) and isinstance(body_map, dict)
        title = title_map.get(lang) or title_map.get("zh-CN") or ""
        body = body_map.get(lang) or body_map.get("zh-CN") or ""
        head = f"**{tag} · {date}** — {title}" if tag else f"**{date} · {title}**"
        lines.append(head)
        lines.append(body)
        lines.append("")
    return "\n".join(lines).strip()

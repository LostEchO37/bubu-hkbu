"""In-app release notes — product-facing only, no private paths/secrets/accounts."""

from __future__ import annotations

from core.i18n import Lang

# Newest first. One entry per public push; wording avoids private ops details.
ENTRIES: list[dict[str, dict[Lang, str] | str]] = [
    {
        "date": "2026-11-04",
        "tag": "v0.29",
        "title": {
            "zh-CN": "菜单错位 + 短链",
            "zh-TW": "選單錯位 + 短鏈",
            "en": "Menu layout + short URL",
        },
        "body": {
            "zh-CN": "· 修好悬浮球泡泡飞到屏幕中间叠成一串的问题\n· 默认改回短链；旧长链自动迁移（长链改名后会 not found）",
            "zh-TW": "· 修好懸浮球泡泡飛到螢幕中間疊成一串的問題\n· 預設改回短鏈；舊長鏈自動遷移（長鏈改名後會 not found）",
            "en": "· Fixed FAB bubbles stacking mid-screen\n· Default back to short Cloud URL; migrate retired hash URLs",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.28",
        "title": {
            "zh-CN": "修复进页一直转圈",
            "zh-TW": "修復進頁一直轉圈",
            "en": "Fix endless loading spinner",
        },
        "body": {
            "zh-CN": "· 悬浮球改走稳定长链，避免短链冷启动卡在加载\n· 冷启动先打开干净页再带参数\n· 修好 pick 参数写回导致的重跑死循环",
            "zh-TW": "· 懸浮球改走穩定長鏈，避免短鏈冷啟動卡在載入\n· 冷啟動先打開乾淨頁再帶參數\n· 修好 pick 參數寫回導致的重跑死循環",
            "en": "· FAB uses the stable long Cloud URL\n· Cold start warms a clean page before deep-link params\n· Fixed pick query rewrite rerun loop",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.27",
        "title": {
            "zh-CN": "悬浮球防遮挡",
            "zh-TW": "懸浮球防遮擋",
            "en": "FAB no clip",
        },
        "body": {
            "zh-CN": "· 功能泡泡只向左上展开，右侧不再被切边\n· 去掉全屏模糊、简化动画；跳转改为单次 tabs.update",
            "zh-TW": "· 功能泡泡只向左上展開，右側不再被切邊\n· 去掉全螢幕模糊、簡化動畫；跳轉改為單次 tabs.update",
            "en": "· Bubbles fan only up-left so the right edge no longer clips them\n· Dropped heavy blur; faster single-tab navigation",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.26",
        "title": {
            "zh-CN": "悬浮球美化 + 减卡顿",
            "zh-TW": "懸浮球美化 + 減卡頓",
            "en": "FAB polish + less lag",
        },
        "body": {
            "zh-CN": "· 去掉残缺 EN 芯片，语言只在展开菜单里切换\n· Cloud 页不再挂悬浮球，减轻抢缓存卡顿\n· 恢复脚本每会话只注入一次",
            "zh-TW": "· 去掉殘缺 EN 芯片，語言只在展開選單切換\n· Cloud 頁不再掛懸浮球，減輕搶快取卡頓\n· 恢復腳本每會話只注入一次",
            "en": "· Removed clipped EN chip; language lives in the radial menu\n· No FAB on Cloud pages (less cache contention)\n· Chunk guard injects once per session",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.25",
        "title": {
            "zh-CN": "修复启动 TypeError",
            "zh-TW": "修復啟動 TypeError",
            "en": "Fix startup TypeError",
        },
        "body": {
            "zh-CN": "· 兼容不同 Streamlit 版本的 st.html 参数，消除启动红字\n· 模块恢复脚本改用更稳妥的注入方式",
            "zh-TW": "· 相容不同 Streamlit 版本的 st.html 參數，消除啟動紅字\n· 模組恢復腳本改用更穩妥的注入方式",
            "en": "· Compatible st.html across Streamlit versions (no startup red error)\n· Chunk-recovery script uses a safer inject path",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.24",
        "title": {
            "zh-CN": "输入框与流畅度",
            "zh-TW": "輸入框與流暢度",
            "en": "Inputs + smoother load",
        },
        "body": {
            "zh-CN": "· 部署后 JS 模块失效会自动软刷新一次\n· 资料区改为按需打开，减轻输入组件抢加载\n· 悬浮球延迟注入、复用已开标签，减少卡顿",
            "zh-TW": "· 部署後 JS 模組失效會自動軟重新整理一次\n· 資料區改為按需打開，減輕輸入元件搶載入\n· 懸浮球延遲注入、重用已開分頁，減少卡頓",
            "en": "· Auto soft-reload once when Streamlit JS chunks fail after deploy\n· Workspace mounts on demand to cut TextInput contention\n· FAB injects later and reuses a warm tab",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.23",
        "title": {
            "zh-CN": "悬浮球 Cloud + 语言",
            "zh-TW": "懸浮球 Cloud + 語言",
            "en": "FAB Cloud URL + language",
        },
        "body": {
            "zh-CN": "· 悬浮球默认打开 Cloud 站，不再指向 localhost\n· 弹窗/设置/球体可切换简繁英，跳转带 lang=",
            "zh-TW": "· 懸浮球預設打開 Cloud 站，不再指向 localhost\n· 彈窗/設定/球體可切換簡繁英，跳轉帶 lang=",
            "en": "· Floating orb defaults to Cloud, not localhost\n· Popup/settings/orb switch zh-CN/zh-TW/en with lang=",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.22",
        "title": {
            "zh-CN": "自定义页签图标",
            "zh-TW": "自訂頁簽圖示",
            "en": "Custom tab icon",
        },
        "body": {
            "zh-CN": "· 浏览器标签页换成阿Bu 气泡图标，不再用 Streamlit 默认红标",
            "zh-TW": "· 瀏覽器分頁換成阿Bu 氣泡圖示，不再用 Streamlit 預設紅標",
            "en": "· Browser tab uses BuBu bubble icon instead of Streamlit red mark",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.21",
        "title": {
            "zh-CN": "上传按钮去黑底",
            "zh-TW": "上傳按鈕去黑底",
            "en": "Upload button clean",
        },
        "body": {
            "zh-CN": "· Upload 按钮去掉多余黑色矩形底\n· 补全用户路径自查脚本",
            "zh-TW": "· Upload 按鈕去掉多餘黑色矩形底\n· 補全用戶路徑自查腳本",
            "en": "· Removed nested black box on Upload\n· Added full user-journey self-check",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.20",
        "title": {
            "zh-CN": "折叠标题对比度",
            "zh-TW": "折疊標題對比度",
            "en": "Expander title contrast",
        },
        "body": {
            "zh-CN": "· 深色模式下折叠栏标题不再白底看不见\n· 输入框外层去掉浅色描边",
            "zh-TW": "· 深色模式下折疊欄標題不再白底看不見\n· 輸入框外層去掉淺色描邊",
            "en": "· Expander titles stay readable on dark surfaces\n· Input wrappers no longer flash light borders",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.19",
        "title": {
            "zh-CN": "深色底部输入区",
            "zh-TW": "深色底部輸入區",
            "en": "Dark chat footer",
        },
        "body": {
            "zh-CN": "· 底部输入条跟随深色主题，不再露出浅色底板\n· 聊天气泡改用主题色，深色下更统一",
            "zh-TW": "· 底部輸入條跟隨深色主題，不再露出淺色底板\n· 聊天氣泡改用主題色，深色下更統一",
            "en": "· Chat footer follows dark theme instead of light Streamlit chrome\n· Chat bubbles use theme tokens for consistent dark mode",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.18",
        "title": {
            "zh-CN": "深色主题保持 + 日志可读",
            "zh-TW": "深色主題保持 + 日誌可讀",
            "en": "Keep dark theme + readable log",
        },
        "body": {
            "zh-CN": "· 登录前选的深色/字号/语气登录后保留\n· 更新日志弹窗在深色模式下提高对比度",
            "zh-TW": "· 登入前選的深色/字級/語氣登入後保留\n· 更新日誌彈窗在深色模式下提高對比度",
            "en": "· Theme/font/tone chosen before login survive sign-in\n· Changelog modal contrast improved for dark mode",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.17",
        "title": {
            "zh-CN": "更新日志弹窗",
            "zh-TW": "更新日誌彈窗",
            "en": "Changelog modal",
        },
        "body": {
            "zh-CN": "· 更新日志改为独立弹窗，不再占版面\n· 入口移到左上，恢复 Fork / GitHub 快捷入口",
            "zh-TW": "· 更新日誌改為獨立彈窗，不再佔版面\n· 入口移到左上，恢復 Fork / GitHub 快捷入口",
            "en": "· Changelog opens in a modal dialog\n· Entry moved top-left; Fork/GitHub restored",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.16",
        "title": {
            "zh-CN": "更新日志可点击",
            "zh-TW": "更新日誌可點擊",
            "en": "Changelog clickable",
        },
        "body": {
            "zh-CN": "· 曾临时处理右上角遮挡（后续已恢复 Fork）\n· 更新日志改为可展开反馈",
            "zh-TW": "· 曾暫時處理右上角遮擋（後續已恢復 Fork）\n· 更新日誌改為可展開回饋",
            "en": "· Temporary overlay workaround (Fork later restored)\n· Changelog open/close feedback",
        },
    },
    {
        "date": "2026-11-04",
        "tag": "v0.15",
        "title": {
            "zh-CN": "更新日志移到右上角",
            "zh-TW": "更新日誌移到右上角",
            "en": "Changelog moved top-right",
        },
        "body": {
            "zh-CN": "· 更新日志改为页面右上角\n· 按每次公开发布补充说明（仅产品改动，不含隐私信息）",
            "zh-TW": "· 更新日誌改為頁面右上角\n· 按每次公開發布補充說明（僅產品改動，不含隱私資訊）",
            "en": "· Changelog moved to the top-right\n· Per-release notes expanded (product-only, privacy-safe)",
        },
    },
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

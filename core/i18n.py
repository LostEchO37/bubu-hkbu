"""UI strings: 简体中文 / 繁體中文 / English."""

from __future__ import annotations

from typing import Literal

Lang = Literal["zh-CN", "zh-TW", "en"]

LANG_OPTIONS: list[tuple[str, Lang]] = [
    ("简体中文", "zh-CN"),
    ("繁體中文", "zh-TW"),
    ("English", "en"),
]

SPEECH_LANG: dict[Lang, str] = {
    "zh-CN": "zh-CN",
    "zh-TW": "zh-HK",
    "en": "en-US",
}

LLM_LANG_HINT: dict[Lang, str] = {
    "zh-CN": "请用简体中文回答。",
    "zh-TW": "請用繁體中文（香港用語習慣）回答。",
    "en": "Reply in English.",
}

MESSAGES: dict[str, dict[Lang, str]] = {
    "app_title": {
        "zh-CN": "HKBU 学生学习助手",
        "zh-TW": "HKBU 學生學習助手",
        "en": "HKBU Student Assistant",
    },
    "app_subtitle": {
        "zh-CN": "浸大校园生活 · 课表规划 · 智能问答",
        "zh-TW": "浸大校園生活 · 課表規劃 · 智能問答",
        "en": "Campus life · Timetable · Smart Q&A",
    },
    "lang_label": {
        "zh-CN": "界面语言",
        "zh-TW": "介面語言",
        "en": "Language",
    },
    "welcome": {
        "zh-CN": "嗨～我是阿Bu，浸大同学助手 🤙 校历、学习规划、CS 实验室都能问。左侧丢课表截图，侧栏「今天」会盯着你下一节课和考试倒计时。",
        "zh-TW": "嗨～我是阿Bu，浸大同學助手 🤙 校曆、溫書規劃、CS 實驗室都可以問。左側 upload 課表，側欄「今天」會睇住你下一堂同考試倒數。",
        "en": "Hey — I'm BuBu, your HKBU buddy 🤙 Calendar, study plans, CS labs. Upload a timetable on the left; the Today panel tracks your next class and exam countdown.",
    },
    "sidebar_profile": {
        "zh-CN": "个性化设置",
        "zh-TW": "個人化設定",
        "en": "Personalisation",
    },
    "name": {"zh-CN": "姓名（可选）", "zh-TW": "姓名（可選）", "en": "Name (optional)"},
    "student_id": {"zh-CN": "学号（可选）", "zh-TW": "學號（可選）", "en": "Student ID (optional)"},
    "programme": {
        "zh-CN": "专业 / 课程",
        "zh-TW": "專業 / 課程",
        "en": "Programme / courses",
    },
    "timetable": {"zh-CN": "课表", "zh-TW": "課表", "en": "Timetable"},
    "tt_hint": {
        "zh-CN": "CSV：course_code,course_name,day,start_time,end_time,location\n或：COMP1234 | Mon 09:30-11:00 | FSC801",
        "zh-TW": "CSV：course_code,course_name,day,start_time,end_time,location\n或：COMP1234 | Mon 09:30-11:00 | FSC801",
        "en": "CSV columns: course_code,course_name,day,start_time,end_time,location\nOr free text: COMP1234 | Mon 09:30-11:00 | FSC801",
    },
    "paste_tt": {"zh-CN": "粘贴课表", "zh-TW": "貼上課表", "en": "Paste timetable"},
    "parse_tt": {"zh-CN": "解析课表", "zh-TW": "解析課表", "en": "Parse timetable"},
    "upload_csv": {"zh-CN": "上传 CSV", "zh-TW": "上傳 CSV", "en": "Upload CSV"},
    "tasks": {"zh-CN": "任务 / 截止日期", "zh-TW": "任務 / 截止日期", "en": "Tasks / deadlines"},
    "new_task": {"zh-CN": "新任务", "zh-TW": "新任務", "en": "New task"},
    "new_due": {"zh-CN": "截止日期（可选）", "zh-TW": "截止日期（可選）", "en": "Due date (optional)"},
    "new_course": {"zh-CN": "相关课程（可选）", "zh-TW": "相關課程（可選）", "en": "Course (optional)"},
    "add_task": {"zh-CN": "添加任务", "zh-TW": "添加任務", "en": "Add task"},
    "email_section": {
        "zh-CN": "邮件截图 → 回复",
        "zh-TW": "郵件截圖 → 回覆",
        "en": "Email screenshot → reply",
    },
    "email_hint": {
        "zh-CN": "上传邮件截图（不连接邮箱）。识别内容并生成可复制的回复草稿。",
        "zh-TW": "上傳郵件截圖（不連接郵箱）。識別內容並生成可複製的回覆草稿。",
        "en": "Upload an email screenshot (no mailbox). Extract content and draft a copyable reply.",
    },
    "upload_email_shot": {
        "zh-CN": "上传邮件截图",
        "zh-TW": "上傳郵件截圖",
        "en": "Upload email screenshot",
    },
    "email_tone": {"zh-CN": "回复语气", "zh-TW": "回覆語氣", "en": "Reply tone"},
    "email_tone_polite": {"zh-CN": "礼貌正式", "zh-TW": "禮貌正式", "en": "Polite"},
    "email_tone_concise": {"zh-CN": "简短", "zh-TW": "簡短", "en": "Concise"},
    "email_tone_friendly": {"zh-CN": "轻松友好", "zh-TW": "輕鬆友好", "en": "Friendly"},
    "scan_email_reply": {
        "zh-CN": "识别并生成回复",
        "zh-TW": "識別並生成回覆",
        "en": "Scan & draft reply",
    },
    "scanning_email": {
        "zh-CN": "正在读截图、起草回复…",
        "zh-TW": "正在讀截圖、起草回覆…",
        "en": "Reading screenshot & drafting reply…",
    },
    "email_vision_fail": {
        "zh-CN": "邮件截图识别失败。请换更清晰的截图再试（尽量含主题与正文）。",
        "zh-TW": "郵件截圖識別失敗。請換更清晰的截圖再試。",
        "en": "Could not read that email screenshot. Try a clearer crop with subject + body.",
    },
    "email_reply_subject": {"zh-CN": "回复主题", "zh-TW": "回覆主題", "en": "Reply subject"},
    "email_reply_body": {"zh-CN": "回复正文（可复制）", "zh-TW": "回覆正文（可複製）", "en": "Reply body (copy)"},
    "email_add_tasks": {
        "zh-CN": "把识别到的截止日期加入任务",
        "zh-TW": "把識別到的截止日期加入任務",
        "en": "Add detected deadlines to tasks",
    },
    "email_ok": {
        "zh-CN": "已生成回复草稿",
        "zh-TW": "已生成回覆草稿",
        "en": "Reply draft ready",
    },
    "plugin_section": {
        "zh-CN": "浏览器悬浮球插件",
        "zh-TW": "瀏覽器懸浮球插件",
        "en": "Floating orb browser extension",
    },
    "plugin_hint": {
        "zh-CN": "下载解压 → 开发者模式加载文件夹 → 扩展「详细信息」把网站访问设为「在所有网站上」。然后任意网页右下角都会有球（chrome:// 除外）。",
        "zh-TW": "下載解壓 → 開發者模式載入 → 網站存取設為「在所有網站上」。任意網頁右下角都會有球。",
        "en": "Load unpacked → set Site access to “On all sites”. Orb appears on any http(s) page (not chrome://).",
    },
    "plugin_download": {
        "zh-CN": "下载悬浮球插件（Windows / Mac）",
        "zh-TW": "下載懸浮球插件（Windows / Mac）",
        "en": "Download floating-orb extension (Windows / Mac)",
    },
    "notes": {
        "zh-CN": "其他备注（如社团、兼职）",
        "zh-TW": "其他備註（如社團、兼職）",
        "en": "Other notes (clubs, part-time, etc.)",
    },
    "ai_settings": {"zh-CN": "AI 设置", "zh-TW": "AI 設定", "en": "AI settings"},
    "api_provider": {"zh-CN": "API 来源", "zh-TW": "API 來源", "en": "API provider"},
    "provider_hkbu": {
        "zh-CN": "HKBU GenAI Platform",
        "zh-TW": "HKBU GenAI Platform",
        "en": "HKBU GenAI Platform",
    },
    "provider_other": {
        "zh-CN": "OpenAI / 其他兼容接口",
        "zh-TW": "OpenAI / 其他兼容接口",
        "en": "OpenAI / compatible API",
    },
    "api_key": {"zh-CN": "API Key", "zh-TW": "API Key", "en": "API Key"},
    "base_url": {"zh-CN": "Base URL", "zh-TW": "Base URL", "en": "Base URL"},
    "model": {"zh-CN": "模型名称", "zh-TW": "模型名稱", "en": "Model name"},
    "test_api": {"zh-CN": "测试 API 连接", "zh-TW": "測試 API 連線", "en": "Test API connection"},
    "export_profile": {
        "zh-CN": "导出个人资料 JSON",
        "zh-TW": "匯出個人資料 JSON",
        "en": "Export profile JSON",
    },
    "import_profile": {
        "zh-CN": "导入个人资料 JSON",
        "zh-TW": "匯入個人資料 JSON",
        "en": "Import profile JSON",
    },
    "plan_week": {
        "zh-CN": "一键生成本周学习计划",
        "zh-TW": "一鍵生成本週學習計劃",
        "en": "Generate this week's study plan",
    },
    "planning": {
        "zh-CN": "正在根据课表与任务规划…",
        "zh-TW": "正在根據課表與任務規劃…",
        "en": "Planning from your timetable and tasks…",
    },
    "chat_placeholder": {
        "zh-CN": "输入问题或安排需求…",
        "zh-TW": "輸入問題或安排需求…",
        "en": "Ask a question or request planning…",
    },
    "voice_section": {"zh-CN": "语音", "zh-TW": "語音", "en": "Voice"},
    "voice_hint": {
        "zh-CN": "使用浏览器语音识别（推荐 Chrome / Edge）。无需升级 HKBU API。",
        "zh-TW": "使用瀏覽器語音識別（建議 Chrome / Edge）。無需升級 HKBU API。",
        "en": "Uses browser speech recognition (Chrome / Edge recommended). No HKBU API upgrade needed.",
    },
    "voice_listen": {"zh-CN": "开始语音输入", "zh-TW": "開始語音輸入", "en": "Start voice input"},
    "voice_listening": {"zh-CN": "正在聆听…", "zh-TW": "正在聆聽…", "en": "Listening…"},
    "voice_unsupported": {
        "zh-CN": "当前浏览器不支持语音输入，请改用 Chrome 或 Edge。",
        "zh-TW": "目前瀏覽器不支援語音輸入，請改用 Chrome 或 Edge。",
        "en": "Voice input not supported in this browser. Try Chrome or Edge.",
    },
    "speak_reply": {"zh-CN": "朗读最新回复", "zh-TW": "朗讀最新回覆", "en": "Read latest reply aloud"},
    "auto_speak": {
        "zh-CN": "自动朗读助手回复",
        "zh-TW": "自動朗讀助手回覆",
        "en": "Auto-read assistant replies",
    },
    "agent_tap": {
        "zh-CN": "点我开聊",
        "zh-TW": "點我開聊",
        "en": "Tap to chat",
    },
    "agent_bubble_hint": {
        "zh-CN": "校历、实验室、辅导预约、复习计划 —— 一句话就行",
        "zh-TW": "校曆、實驗室、輔導預約、複習計劃 —— 一句話就行",
        "en": "Calendar, labs, counselling, study plans — just ask",
    },
    "hub_brand": {
        "zh-CN": "阿Bu · HKBU",
        "zh-TW": "阿Bu · HKBU",
        "en": "BuBu · HKBU",
    },
    "hub_title_1": {
        "zh-CN": "阿Bu",
        "zh-TW": "阿Bu",
        "en": "BuBu",
    },
    "hub_title_2": {
        "zh-CN": "同学助手",
        "zh-TW": "同學助手",
        "en": "Campus Buddy",
    },
    "hub_cta": {
        "zh-CN": "开始聊聊",
        "zh-TW": "開始聊聊",
        "en": "Let's chat",
    },
    "hub_credit": {
        "zh-CN": "proudly presented by GTSC2066 Group 16",
        "zh-TW": "proudly presented by GTSC2066 Group 16",
        "en": "proudly presented by GTSC2066 Group 16",
    },
    "fab_tip": {
        "zh-CN": "点开功能球",
        "zh-TW": "點開功能球",
        "en": "Open feature orb",
    },
    "fab_close": {"zh-CN": "收起", "zh-TW": "收起", "en": "Close"},
    "fab_chat": {"zh-CN": "开聊", "zh-TW": "開聊", "en": "Chat"},
    "fab_plan": {"zh-CN": "计划", "zh-TW": "計劃", "en": "Plan"},
    "fab_tt": {"zh-CN": "课表", "zh-TW": "課表", "en": "Timetable"},
    "fab_mail": {"zh-CN": "回信", "zh-TW": "回信", "en": "Reply"},
    "fab_task": {"zh-CN": "任务", "zh-TW": "任務", "en": "Tasks"},
    "fab_panel_tt": {
        "zh-CN": "识别课表截图",
        "zh-TW": "識別課表截圖",
        "en": "Scan timetable screenshot",
    },
    "fab_panel_mail": {
        "zh-CN": "邮件截图 → 回复草稿",
        "zh-TW": "郵件截圖 → 回覆草稿",
        "en": "Email screenshot → reply draft",
    },
    "fab_panel_task": {
        "zh-CN": "添加任务",
        "zh-TW": "添加任務",
        "en": "Add a task",
    },
    "fab_panel_close": {
        "zh-CN": "关闭面板",
        "zh-TW": "關閉面板",
        "en": "Close panel",
    },
    "pulse_today": {"zh-CN": "今天", "zh-TW": "今天", "en": "Today"},
    "pulse_countdown": {"zh-CN": "倒计时", "zh-TW": "倒數", "en": "Countdown"},
    "pulse_tasks": {"zh-CN": "近期任务", "zh-TW": "近期任務", "en": "Tasks"},
    "pulse_remind": {"zh-CN": "提醒", "zh-TW": "提醒", "en": "Alerts"},
    "day_mon": {"zh-CN": "周一", "zh-TW": "週一", "en": "Mon"},
    "day_tue": {"zh-CN": "周二", "zh-TW": "週二", "en": "Tue"},
    "day_wed": {"zh-CN": "周三", "zh-TW": "週三", "en": "Wed"},
    "day_thu": {"zh-CN": "周四", "zh-TW": "週四", "en": "Thu"},
    "day_fri": {"zh-CN": "周五", "zh-TW": "週五", "en": "Fri"},
    "day_sat": {"zh-CN": "周六", "zh-TW": "週六", "en": "Sat"},
    "day_sun": {"zh-CN": "周日", "zh-TW": "週日", "en": "Sun"},
    "today_no_tt": {
        "zh-CN": "还没课表 — 上传截图后这里会亮起来。",
        "zh-TW": "未有課表 — 上傳截圖後這裡會亮起。",
        "en": "No timetable yet — upload a screenshot to light this up.",
    },
    "today_free_day": {
        "zh-CN": "今天没有课，适合复习或摸鱼（二选一）。",
        "zh-TW": "今日無課，適合溫書或休息。",
        "en": "No classes today — revise or rest.",
    },
    "today_done": {
        "zh-CN": "今天的课都上完啦。",
        "zh-TW": "今日的課都上完啦。",
        "en": "You're done with classes today.",
    },
    "today_next_in": {
        "zh-CN": "下一节 {code} 还有 {n} 分钟 · {time} @ {loc}",
        "zh-TW": "下一堂 {code} 仲有 {n} 分鐘 · {time} @ {loc}",
        "en": "Next: {code} in {n} min · {time} @ {loc}",
    },
    "today_next_now": {
        "zh-CN": "马上开始：{code} · {time} @ {loc}",
        "zh-TW": "即將開始：{code} · {time} @ {loc}",
        "en": "Starting now: {code} · {time} @ {loc}",
    },
    "today_in_class": {
        "zh-CN": "正在上课：{code} · 到 {end} @ {loc}",
        "zh-TW": "正在上課：{code} · 到 {end} @ {loc}",
        "en": "In class: {code} · until {end} @ {loc}",
    },
    "today_gaps": {
        "zh-CN": "今日空档：{gaps}",
        "zh-TW": "今日空檔：{gaps}",
        "en": "Free today: {gaps}",
    },
    "today_no_tasks": {
        "zh-CN": "暂无任务 — 侧栏可以加一条。",
        "zh-TW": "暫無任務 — 側欄可以加一條。",
        "en": "No tasks yet — add one in the sidebar.",
    },
    "countdown_none": {
        "zh-CN": "近期校历节点已过完",
        "zh-TW": "近期校曆節點已過完",
        "en": "No upcoming calendar milestones",
    },
    "countdown_exam_sem1": {
        "zh-CN": "第一学期考试周",
        "zh-TW": "第一學期考試週",
        "en": "Sem 1 exam period",
    },
    "countdown_exam_sem2": {
        "zh-CN": "第二学期考试周",
        "zh-TW": "第二學期考試週",
        "en": "Sem 2 exam period",
    },
    "countdown_last_class_sem1": {
        "zh-CN": "第一学期最后上课日",
        "zh-TW": "第一學期最後上課日",
        "en": "Sem 1 last teaching day",
    },
    "countdown_last_class_sem2": {
        "zh-CN": "第二学期最后上课日",
        "zh-TW": "第二學期最後上課日",
        "en": "Sem 2 last teaching day",
    },
    "countdown_in_days": {
        "zh-CN": "{label} · 还有 {n} 天（{dates}）",
        "zh-TW": "{label} · 仲有 {n} 日（{dates}）",
        "en": "{label} · {n} day(s) left ({dates})",
    },
    "countdown_ongoing": {
        "zh-CN": "{label} · 进行中（{dates}）",
        "zh-TW": "{label} · 進行中（{dates}）",
        "en": "{label} · ongoing ({dates})",
    },
    "remind_none": {
        "zh-CN": "暂无赶场/冲突提醒，课表看起来还行。",
        "zh-TW": "暫無趕場/衝突提醒，課表睇落都 OK。",
        "en": "No rush or clash alerts — schedule looks fine.",
    },
    "remind_rush": {
        "zh-CN": "{day} 跨楼赶场（课间 {gap} 分钟）：{a}（{from_b}）→ {b}（{to_b}）",
        "zh-TW": "{day} 跨樓趕場（課間 {gap} 分鐘）：{a}（{from_b}）→ {b}（{to_b}）",
        "en": "{day} cross-building rush ({gap} min break): {a} ({from_b}) → {b} ({to_b})",
    },
    "remind_overlap": {
        "zh-CN": "{day} 时段重叠：{a} {t1} 与 {b} {t2}",
        "zh-TW": "{day} 時段重疊：{a} {t1} 與 {b} {t2}",
        "en": "{day} clash: {a} {t1} vs {b} {t2}",
    },
    "burst_pick_hint": {
        "zh-CN": "选一个话题，开始聊天",
        "zh-TW": "選一個話題，開始聊天",
        "en": "Pick a topic to start chatting",
    },
    "tt_gaps_caption": {
        "zh-CN": "空档已算好，聊天直接问复习安排即可。",
        "zh-TW": "空檔已算好，聊天直接問複習安排即可。",
        "en": "Free slots computed — ask for a study plan in chat.",
    },
    "q1": {
        "zh-CN": "这学期校历里考试周是什么时候？",
        "zh-TW": "這學期校曆裏考試週是什麼時候？",
        "en": "When is the exam period this semester?",
    },
    "q2": {
        "zh-CN": "CS 实验室 FSC801 开放时间？",
        "zh-TW": "CS 實驗室 FSC801 開放時間？",
        "en": "What are FSC801 CS lab opening hours?",
    },
    "q3": {
        "zh-CN": "根据我的课表，帮我安排本周复习计划",
        "zh-TW": "根據我的課表，幫我安排本週複習計劃",
        "en": "Plan my revision this week from my timetable",
    },
    "q4": {
        "zh-CN": "浸大 counselling 怎么预约？",
        "zh-TW": "浸大 counselling 怎麼預約？",
        "en": "How do I book HKBU counselling?",
    },
    "imported_slots": {
        "zh-CN": "已导入 {n} 个时段",
        "zh-TW": "已匯入 {n} 個時段",
        "en": "Imported {n} slot(s)",
    },
    "parse_fail": {
        "zh-CN": "未能识别课表，请检查格式",
        "zh-TW": "未能識別課表，請檢查格式",
        "en": "Could not parse timetable — check format",
    },
    "task_added": {"zh-CN": "已添加", "zh-TW": "已添加", "en": "Added"},
    "profile_imported": {
        "zh-CN": "已导入资料",
        "zh-TW": "已匯入資料",
        "en": "Profile imported",
    },
    "login_title": {
        "zh-CN": "登录 / 注册",
        "zh-TW": "登入 / 註冊",
        "en": "Log in / Sign up",
    },
    "login_hint": {
        "zh-CN": "用学号或邮箱注册，课表和任务会保存在云端（本机数据库），换设备登录即可同步。",
        "zh-TW": "用學號或電郵註冊，課表和任務會保存，換裝置登入即可同步。",
        "en": "Sign up with student ID or email — your timetable syncs when you log in elsewhere.",
    },
    "tab_login": {"zh-CN": "登录", "zh-TW": "登入", "en": "Log in"},
    "tab_register": {"zh-CN": "注册", "zh-TW": "註冊", "en": "Sign up"},
    "username": {"zh-CN": "用户名（学号 / 邮箱）", "zh-TW": "用戶名（學號 / 電郵）", "en": "Username (ID / email)"},
    "password": {"zh-CN": "密码", "zh-TW": "密碼", "en": "Password"},
    "display_name": {"zh-CN": "昵称（可选）", "zh-TW": "暱稱（可選）", "en": "Nickname (optional)"},
    "btn_login": {"zh-CN": "进入助手", "zh-TW": "進入助手", "en": "Enter assistant"},
    "btn_register": {"zh-CN": "创建账号", "zh-TW": "建立帳號", "en": "Create account"},
    "logout": {"zh-CN": "退出登录", "zh-TW": "登出", "en": "Log out"},
    "synced": {
        "zh-CN": "已同步到账号",
        "zh-TW": "已同步到帳號",
        "en": "Saved to your account",
    },
    "auth_invalid": {
        "zh-CN": "用户名或密码不正确",
        "zh-TW": "用戶名或密碼不正確",
        "en": "Invalid username or password",
    },
    "auth_taken": {
        "zh-CN": "用户名已被注册",
        "zh-TW": "用戶名已被註冊",
        "en": "Username already taken",
    },
    "auth_short_user": {
        "zh-CN": "用户名至少 3 个字符",
        "zh-TW": "用戶名至少 3 個字元",
        "en": "Username must be at least 3 characters",
    },
    "auth_short_pass": {
        "zh-CN": "密码至少 6 位",
        "zh-TW": "密碼至少 6 位",
        "en": "Password must be at least 6 characters",
    },
    "register_ok": {
        "zh-CN": "注册成功，正在进入…",
        "zh-TW": "註冊成功，正在進入…",
        "en": "Account created — signing you in…",
    },
    "upload_tt_image": {
        "zh-CN": "上传课表截图",
        "zh-TW": "上傳課表截圖",
        "en": "Upload timetable screenshot",
    },
    "scan_tt": {
        "zh-CN": "AI 识别课表",
        "zh-TW": "AI 識別課表",
        "en": "Scan timetable with AI",
    },
    "scanning_tt": {
        "zh-CN": "正在读你的课表…",
        "zh-TW": "正在讀你的課表…",
        "en": "Reading your timetable…",
    },
    "tt_image_tip": {
        "zh-CN": "上传后会自动识别；也可再点下方按钮。聊天框收不到图片。",
        "zh-TW": "上傳後會自動識別；聊天框收不到圖片。",
        "en": "Uploads auto-scan (or tap the button). Chat cannot receive images.",
    },
    "vision_fail": {
        "zh-CN": "课表解析失败（多为模型输出不完整）。请再点一次「AI 识别课表」；仍失败再检查 OPENAI_VISION_MODEL 是否支持识图。",
        "zh-TW": "課表解析失敗（多為模型輸出不完整）。請再試一次識別；仍失敗請檢查識圖模型設定。",
        "en": "Timetable parse failed (often truncated model JSON). Try scan again, or check OPENAI_VISION_MODEL.",
    },
    "tt_scan_ok_chat": {
        "zh-CN": "课表已录入（{n} 节）～ 可以直接问我空档、冲突或复习安排，不用再往对话框里塞截图。",
        "zh-TW": "課表已錄入（{n} 節）～ 可以直接問我空檔或複習安排，不用再往對話框塞截圖。",
        "en": "Timetable saved ({n} slots). Ask about free time or study plans — no need to attach images in chat.",
    },
    "tt_ready_hint": {
        "zh-CN": "已进个人资料：聊天里问课表即可，助手必须按上面列表回答。",
        "zh-TW": "已進個人資料：聊天問課表即可。",
        "en": "Saved to your profile — ask in chat; the assistant must use this list.",
    },
    "more_options": {"zh-CN": "更多（备注）", "zh-TW": "更多（備註）", "en": "More (notes)"},
    "email_summary_label": {"zh-CN": "摘要", "zh-TW": "摘要", "en": "Summary"},
    "logged_as": {"zh-CN": "已登录：{name}", "zh-TW": "已登入：{name}", "en": "Signed in as {name}"},
    "settings_title": {"zh-CN": "设置", "zh-TW": "設定", "en": "Settings"},
    "settings_font": {"zh-CN": "字体大小", "zh-TW": "字體大小", "en": "Font size"},
    "font_small": {"zh-CN": "小", "zh-TW": "小", "en": "Small"},
    "font_medium": {"zh-CN": "中", "zh-TW": "中", "en": "Medium"},
    "font_large": {"zh-CN": "大", "zh-TW": "大", "en": "Large"},
    "settings_theme": {"zh-CN": "外观", "zh-TW": "外觀", "en": "Appearance"},
    "theme_light": {"zh-CN": "浅色", "zh-TW": "淺色", "en": "Light"},
    "theme_dark": {"zh-CN": "深色", "zh-TW": "深色", "en": "Dark"},
    "settings_personality": {"zh-CN": "助手性格", "zh-TW": "助手性格", "en": "Assistant tone"},
    "personality_playful": {"zh-CN": "调皮", "zh-TW": "調皮", "en": "Playful"},
    "personality_balanced": {"zh-CN": "平衡", "zh-TW": "平衡", "en": "Balanced"},
    "personality_calm": {"zh-CN": "收敛", "zh-TW": "收斂", "en": "Calm"},
    "settings_apply": {"zh-CN": "应用设置", "zh-TW": "套用設定", "en": "Apply settings"},
    "save_profile": {"zh-CN": "保存个人资料", "zh-TW": "保存個人資料", "en": "Save profile"},
    "profile_saved": {"zh-CN": "已保存", "zh-TW": "已保存", "en": "Saved"},
    "new_chat": {"zh-CN": "新对话", "zh-TW": "新對話", "en": "New chat"},
}


def t(key: str, lang: Lang, **fmt: object) -> str:
    entry = MESSAGES.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get("zh-CN") or key
    if fmt:
        try:
            return text.format(**fmt)
        except (KeyError, ValueError):
            return text
    return text

# GTSC 2066 Group Project — HKBU Student Assistant  
## 项目搭建与开发流程说明

**课程：** GTSC 2066 Generative AI and Its Applications  
**项目类型：** Group Project  
**文档版本：** 2026-10-29  

---

## 1. 项目概述

### 1.1 问题与目标
浸大学生日常需要查询校历、校园服务、课表安排与学习任务。通用 ChatGPT 缺乏浸大本地资料，也无法记住个人课表。本项目构建 **HKBU Student Assistant**：面向浸大学生的 Web 对话助手，结合 **RAG 知识库**、**账号同步的个人资料** 与 **HKBU GenAI Platform API**。

### 1.2 核心功能
| 功能 | 说明 |
|------|------|
| 多语言 UI | 简体中文 / 繁體中文 / English |
| 账号系统 | 注册登录，SQLite 保存课表、任务、聊天记录 |
| 课表识别 | 上传课表 **截图**，多模态模型解析为结构化课表 |
| 校园问答 | 内置 2026–27 校历、校园 FAQ、CS 技术支持知识库 |
| 学习规划 | 结合课表与任务生成本周学习计划 |
| 设置 | 字体大小、浅/深色、助手性格（调皮 / 平衡 / 收敛） |

### 1.3 非目标（当前版本）
- 非 BUniPort 官方 SSO（课程 demo 使用自建账号）
- 非实时 Siri 式语音双工对话
- API Key 不对终端用户展示（仅服务器 `.env` / Secrets）

---

## 2. 技术架构

- **前端：** Streamlit（`app.py`）— 登录、课表上传、聊天、设置  
- **AI 层：** `core/agent.py` — 组装 RAG、人设、用户资料，调用 GenAI API  
- **知识库：** `data/knowledge/` — 校历、FAQ、CS 支持文档  
- **用户数据：** SQLite `data/users.db` — 账号、课表 JSON、聊天历史  
- **外部服务：** HKBU GenAI `https://genai.hkbu.edu.hk/api/v1/chat/completions`

**每轮对话注入（Always-on context）：**
1. **当前对话用户** — 完整课表、任务、备注（`mandatory_profile_context`）
2. **浸大固定资料** — 中文校历 + 校园 FAQ（`mandatory_bootstrap`）
3. **检索补充** — 按问题关键词扩展检索（`search_knowledge`）

---

## 3. 开发阶段（实际搭建流程）

### Phase 1 — 需求与资料收集（第 1 周）
1. 确定用户故事：校历问答、课表规划、校园生活、CS 实验室等。
2. 收集权威资料：
   - Academic Registry 校历 PDF（2026–27）
   - HKBU 官网 / SA / ITO 公开页面
   - 课程提供的 CS Technical Support Knowledge Base
3. 确认 AI 接口：**HKBU GenAI Platform**（`https://genai.hkbu.edu.hk/api/v1`）+ REST API Key。

### Phase 2 — 原型（第 2 周）
1. 初始化 Python 项目与 Streamlit 界面。
2. 接入 GenAI API（Bearer Token），完成基础对话。
3. 建立 `data/knowledge/`，将 PDF 转为 `.md` / `.txt`。
4. 实现关键词检索 RAG（`core/knowledge.py`）。

### Phase 3 — 个性化（第 3 周）
1. 设计 `StudentProfile`（课表、任务、邮件摘要）。
2. 课表：从 CSV/文本改为 **截图 + Vision 模型**（`gemini-3.8-flash`）。
3. SQLite 账号与云端同步（`core/auth.py`, `core/database.py`）。

### Phase 4 — 体验与交付（第 4 周）
1. UI：浸大天蓝 + 奶白、宋体、设置面板。
2. 人设：同学语气 + 三档性格；多语言问候同步。
3. 安全：API Key 移出 UI，仅 `.env` / Streamlit Secrets。
4. 测试、文档、演示脚本。

---

## 4. 目录结构

```
hkbu-student-assistant/
├── app.py                 # Streamlit 入口
├── requirements.txt
├── .env                   # 本地密钥（勿提交 Git）
├── core/
│   ├── agent.py           # LLM 调用与上下文组装
│   ├── knowledge.py       # RAG + 固定注入
│   ├── profile.py         # 用户资料与课表
│   ├── auth.py / database.py
│   ├── timetable_vision.py
│   ├── i18n.py / persona.py / app_settings.py
│   └── ui.py              # 主题 CSS
├── data/
│   ├── knowledge/         # 知识库文件
│   └── users.db           # 用户数据（运行时生成）
└── docs/                  # 说明与 PDF
```

---

## 5. 环境搭建（逐步操作）

### 5.1 前置条件
- macOS / Windows / Linux
- Python 3.10+
- HKBU GenAI Platform 账号与 **Active API Key**
- 模型：`deepSeek-V4-Pro-hkbu`（对话）、`gemini-3.8-flash`（课表识图）

### 5.2 安装步骤
```bash
cd hkbu-student-assistant
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5.3 配置 `.env`（示例）
```env
LLM_PROVIDER=hkbu
OPENAI_API_KEY=你的-uuid-key
OPENAI_BASE_URL=https://genai.hkbu.edu.hk/api/v1
OPENAI_MODEL=deepSeek-V4-Pro-hkbu
OPENAI_VISION_MODEL=gemini-3.8-flash
```

### 5.4 启动
```bash
streamlit run app.py
```
浏览器访问 `http://localhost:8501` → 注册 → 登录 → 上传课表截图 → 对话测试。

### 5.5 对外部署（小组交付建议）
- **Streamlit Community Cloud** 或学校服务器
- 在平台 **Secrets** 中配置上述环境变量（勿上传 `.env`）
- 数据库 `users.db` 需在服务器持久化卷上，否则重启丢失用户

---

## 6. 知识库维护

1. 新增 `.md` / `.txt` 至 `data/knowledge/`。
2. 中文校历务必包含「考试周」等中文关键词（便于检索）。
3. 更新后重启 Streamlit，无需「训练」大模型。

---

## 7. 测试清单（演示前）

- [ ] 登录 / 注册 / 换设备登录后课表仍在
- [ ] 问「这学期考试周」→ 2026-12-07 至 12-19
- [ ] 问「FSC801 开放时间」→ 来自 CS 知识库
- [ ] 上传课表截图 → AI 识别 → 问「我周几有空」
- [ ] 切换 English → 问候语变英文
- [ ] 设置：深色模式、字体、性格切换
- [ ] 侧边栏无 API Key 输入框

---

## 8. 风险与局限

| 项 | 说明 |
|----|------|
| LLM 幻觉 | 以知识库为准；系统 prompt 禁止谎称无校历 |
| Vision 误识别 | 需清晰完整课表截图 |
| 账号安全 | Demo 级 PBKDF2；生产需 HTTPS + 更强策略 |
| 多机同步 | 需部署到同一后端数据库 |

---

## 9. 小组分工建议（可写入报告）

| 角色 | 职责 |
|------|------|
| PM / 文档 | 需求、本 PDF、演示稿 |
| 后端 / AI | agent、RAG、GenAI 接入 |
| 前端 / UX | Streamlit UI、i18n、主题 |
| 数据 | 校历、FAQ 整理、测试用例 |

---

## 10. 参考文献与链接

- HKBU GenAI Platform: https://genai.hkbu.edu.hk  
- University Calendar: https://calendar.ar.hkbu.edu.hk/  
- Streamlit Documentation: https://docs.streamlit.io  

---

*本文件由项目组维护，与仓库 `hkbu-student-assistant` 同步。*

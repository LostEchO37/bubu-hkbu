# 需要接什么 API？（HKBU Student Assistant）

这个 chatbot **只需要一个「大模型对话 API」** 就能完整运行。校历、校园资料、课表、邮件粘贴都在本地处理，**不需要** BUniPort 接口。

## 推荐：HKBU GenAI Platform（你截图里的 REST API key）

1. 打开 [genai.hkbu.edu.hk](https://genai.hkbu.edu.hk) → **Settings** → **REST API credential**。
2. 若页面显示 **「Active API key · Created …」**，表示 **已经激活**，可直接使用（无需再点开通）。
3. 点击 **Copy** 复制 key（只显示一次时务必立刻保存）。
4. 文档里的 **Base URL** 一般是：`https://genai.hkbu.edu.hk/api/v1`（就是你截图那一行）。
5. 同一页示例 JSON 里的 **`model`** 字段（例如某个 GPT/Claude 部署名）填到 chatbot 侧边栏 **模型名称**。
6. 运行 `streamlit run app.py`，选 **HKBU GenAI Platform**，粘贴 API Key + Base URL + 模型名，点 **测试 API 连接**。

环境变量方式：

```bash
export LLM_PROVIDER=hkbu
export OPENAI_API_KEY="你的-uuid-key"
export OPENAI_BASE_URL="https://genai.hkbu.edu.hk/api/v1"
export OPENAI_MODEL="文档示例里的-model-名"
streamlit run app.py
```

**安全：** 不要把 key 发给他人或提交到 GitHub；截图里若已暴露 key，可在同一页 **Rotate API key** 换新。

---

## 备选：OpenAI 或兼容接口

任选一种方式提供密钥：

### 方式 A：界面里填（最简单）

1. 运行 `streamlit run app.py`
2. 左侧 **AI 设置 → OpenAI API Key** 粘贴密钥  
3. 直接开始聊天

### 方式 B：环境变量（推荐长期使用）

在项目目录创建 `.env`（不要提交到 git）：

```bash
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

终端启动前：

```bash
export OPENAI_API_KEY="sk-xxxxxxxx"
streamlit run app.py
```

### 密钥从哪里拿？

| 提供商 | 步骤 |
| --- | --- |
| **OpenAI** | 注册 [platform.openai.com](https://platform.openai.com) → API keys → Create key；账户需有余额或绑卡 |
| **Azure OpenAI** | Azure 门户创建 OpenAI 资源 → Keys and Endpoint；设置 `OPENAI_BASE_URL` 为你的 endpoint + `/openai/v1/`，模型名用部署名 |
| **DeepSeek 等** | 在服务商控制台创建 API Key；`OPENAI_BASE_URL` 填其文档中的 OpenAI 兼容地址，`OPENAI_MODEL` 填对应模型名 |

侧边栏 **API Base URL** 仅在使用非 OpenAI 官方地址时需要填写。

## 不需要接的 API

| 功能 | 说明 |
| --- | --- |
| 校历 PDF | 已放入 `data/knowledge/`，本地检索，无需 API |
| 课表 / 任务 | 用户输入，存于浏览器 session |
| 邮件截图回复 | 侧栏或扩展「回信」打开面板，上传截图生成回复草稿（不连接邮箱） |
| 浏览器悬浮球 | `extension/` Chrome/Edge 扩展；页面角悬浮球跳转开聊/课表/计划/回信/任务 |
| HKBU BUniPort | 无公开学生 API；课表请手动导出或粘贴 |

## 可选扩展（以后若要）

- **向量数据库 + Embedding API**：课表很多时，可把 `core/knowledge.py` 换成 embedding 检索（当前关键词检索对校历 FAQ 已够用）

## 费用大概多少？

- 使用 `gpt-4o-mini` 时，一般日常问答 + 学习计划 **每次几分钱港币量级**（视对话长度而定）
- 可在 OpenAI 后台设置 **Usage limits / 预算上限**

## 安全提醒

- 不要把 API Key 写进作业 PDF 或公开 GitHub  
- 学号、课表导出 JSON 仅保存在本机 Streamlit session，除非你点击「导出个人资料」

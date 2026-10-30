# HKBU Student Assistant

GTSC 2066 小组项目：浸大学生学习与生活 AI 助手（Streamlit + HKBU GenAI + RAG）。

## 功能摘要

- 三语 UI、浅/深色、字体与助手性格设置
- 账号登录，课表 / 任务 / 聊天记录同步（SQLite）
- 课表 **截图** AI 识别
- 内置 2026–27 校历与校园 FAQ（每轮对话强制注入模型上下文）
- API Key 仅服务器配置，不对用户展示

## 快速开始

```bash
cd hkbu-student-assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填入 GenAI API Key
streamlit run app.py
```

## 小组项目文档（PDF）

完整搭建流程见：

- Markdown: [docs/GTSC2066_Group_Project_Build_Guide.md](docs/GTSC2066_Group_Project_Build_Guide.md)
- PDF: [docs/GTSC2066_Group_Project_Build_Guide.pdf](docs/GTSC2066_Group_Project_Build_Guide.pdf)

生成 PDF：

```bash
pip install fpdf2
python scripts/generate_build_guide_pdf.py
```

## 其他文档

- [docs/API_SETUP.md](docs/API_SETUP.md) — GenAI API 与部署密钥

## 免责声明

回答仅供参考，以 [Academic Registry](https://calendar.ar.hkbu.edu.hk/) 为准。

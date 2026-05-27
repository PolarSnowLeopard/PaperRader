<div align="center">

# PaperRader

### AI 驱动的学术论文管理平台

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3.5+-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](#docker-部署)

**采集、组织、搜索、分析学术论文，AI 全程辅助。**

[English](README.md) | [中文](README_CN.md)

</div>

---

## 项目简介

PaperRader 是一个 **AI 原生的学术论文管理平台** —— 可以理解为 **Zotero + AI**。它帮助研究者从多个来源采集论文、在工作空间中组织管理、自动生成阅读报告，并支持对论文集合进行智能问答。

> **说明：** 项目正在积极开发中，当前版本为早期框架，核心功能已可用。未来计划不仅限于管理系统本身，还会以独立技能（Skills）、CLI 工具、插件等形式发布更多研究辅助工具。

<!-- 
## 截图

> TODO: 添加主界面、论文详情、AI 对话等截图
-->

## 核心功能

**工作空间管理** — 通过工作空间和嵌套文件夹灵活组织论文

**多源导入** — 支持 arXiv、Semantic Scholar 搜索导入，DOI 导入，PDF 上传

**内嵌 PDF 阅读** — 左侧 PDF 阅读，右侧笔记与 AI 分析面板

**AI 阅读报告** — 基于论文全文自动生成结构化阅读报告，支持追问

**跨论文 RAG 问答** — 对工作空间内所有论文进行检索增强生成（RAG）对话

**智能搜索** — 自然语言描述需求，LLM 理解意图并智能排序

**顶会监控** — 同步 ICLR、NeurIPS、ICML、ACL、EMNLP 等顶会论文，提供统计分析

## 系统架构

```
┌──────────────────────────────────────────────────────┐
│                   前端 (Vue 3)                        │
│          Ant Design Vue · Vite · Vue Router          │
├──────────────────────────────────────────────────────┤
│                       /api                           │
├──────────────────────────────────────────────────────┤
│                  后端 (FastAPI)                       │
│  ┌─────────┐  ┌──────────┐  ┌─────────────────────┐ │
│  │ 路由层  │→ │ 服务层   │→ │ 模型层 (SQLAlchemy) │ │
│  └─────────┘  └──────────┘  └─────────────────────┘ │
│       │            │                    │            │
│  ┌────┴────┐  ┌────┴─────┐     ┌───────┴──────┐    │
│  │ Schema  │  │ LLM/RAG  │     │ SQLite/MySQL │    │
│  │(Pydantic)│  │ (litellm)│     │   + PDF存储  │    │
│  └─────────┘  └──────────┘     └──────────────┘    │
├──────────────────────────────────────────────────────┤
│                  数据采集 & 富化                      │
│    arXiv · Semantic Scholar · OpenReview · ACL       │
└──────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.11+，推荐使用 [uv](https://docs.astral.sh/uv/) 管理
- Node.js 18+
- LLM API Key（支持 [litellm](https://docs.litellm.ai/) 的任意提供商）

### 方式一：Docker 部署（推荐）

```bash
git clone https://github.com/PolarSnowLeopard/PaperRader.git
cd PaperRader

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 启动服务
docker compose up -d

# 访问 http://localhost:3000
```

### 方式二：手动安装

```bash
git clone https://github.com/PolarSnowLeopard/PaperRader.git
cd PaperRader

# 后端
uv sync
cp .env.example .env   # 编辑填入 API Key
uv run paperader init-db
uv run paperader serve  # API 服务 http://localhost:8001

# 前端（新终端）
cd frontend
npm install
npm run dev             # 前端 http://localhost:5173
```

## 项目结构

```
PaperRader/
├── paperader/                 # Python 核心包
│   ├── collectors/            #   论文数据源（arXiv、S2、OpenReview、ACL）
│   ├── llm/                   #   LLM 客户端 & Prompt 模板
│   ├── models/                #   SQLAlchemy ORM 模型
│   ├── search/                #   智能搜索（意图理解 → 过滤 → 排序）
│   ├── services/              #   业务逻辑（导入、分块、报告、对话）
│   └── config.py              #   配置管理（pydantic-settings）
├── server/                    # FastAPI 应用
│   ├── routers/               #   API 路由
│   └── schemas/               #   Pydantic 请求/响应模型
├── frontend/                  # Vue 3 + Vite 单页应用
│   └── src/
│       ├── api/               #   Axios API 客户端
│       ├── views/             #   页面组件
│       └── styles/            #   全局 CSS 设计系统
├── scripts/                   # 运维脚本
├── docker-compose.yml         # 容器编排
├── Dockerfile                 # 后端镜像
└── pyproject.toml             # Python 项目配置
```

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic |
| **前端** | Vue 3, Vite, Ant Design Vue, md-editor-v3 |
| **LLM** | litellm（支持 OpenAI, Gemini, Claude 等） |
| **数据库** | SQLite（开发）/ MySQL（生产） |
| **PDF 处理** | PyMuPDF（文本提取与分块） |
| **数据源** | arXiv API, Semantic Scholar, OpenReview, ACL Anthology, CrossRef |
| **部署** | Docker Compose, GitHub Actions, Nginx |

## 路线图

PaperRader 不仅是论文管理工具，更是一个持续进化的研究工具平台：

- [ ] PDF 标注与高亮
- [ ] 引用关系图谱可视化
- [ ] 论文推荐引擎
- [ ] 独立 CLI 工具（论文采集与分析）
- [ ] 可插拔技能系统（Skills）
- [ ] 浏览器插件（一键收藏论文）
- [ ] 多用户协作与共享工作空间

## 参与贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 开源协议

本项目基于 MIT 协议开源 — 详见 [LICENSE](LICENSE)。

---

<div align="center">
  <sub>为研究社区而生，以咖啡和好奇心驱动。</sub>
</div>

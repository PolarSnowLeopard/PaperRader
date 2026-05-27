<div align="center">

# PaperRader

### AI-Powered Research Paper Management Platform

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3.5+-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](#docker-deployment)

**Collect, organize, search, and analyze academic papers with AI assistance.**

[English](README.md) | [中文](README_CN.md)

</div>

---

## What is PaperRader?

PaperRader is an AI-native research paper management platform — think **Zotero meets AI**. It helps researchers collect papers from multiple sources, organize them in workspaces, generate reading reports, and have intelligent conversations about their paper collections.

> **Note:** This project is under active development. The current release is an early-stage framework — the core features are functional but more advanced capabilities are being built. Future plans include standalone skills, CLI tools, and plugins that extend beyond the main system.

<!-- 
## Screenshots

> TODO: Add screenshots of the main interface, paper detail view, AI chat, etc.
-->

## Features

**Workspace Management** — Organize papers into workspaces with nested folder hierarchies

**Multi-Source Import** — Import from arXiv, Semantic Scholar, DOI, or upload PDFs directly

**Embedded PDF Reader** — Read papers inline with a side panel for notes and AI analysis

**AI Reading Reports** — Generate structured reports from full paper text with follow-up Q&A

**Cross-Paper RAG Chat** — Ask questions across all papers in a workspace using retrieval-augmented generation

**Smart Search** — Natural language search with LLM-powered intent understanding and ranking

**Conference Monitoring** — Sync papers from top venues (ICLR, NeurIPS, ICML, ACL, EMNLP) with analytics

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Frontend (Vue 3)                    │
│         Ant Design Vue · Vite · Vue Router           │
├──────────────────────────────────────────────────────┤
│                        /api                          │
├──────────────────────────────────────────────────────┤
│                  Backend (FastAPI)                    │
│  ┌─────────┐  ┌──────────┐  ┌─────────────────────┐ │
│  │ Routers │→ │ Services │→ │ Models (SQLAlchemy) │ │
│  └─────────┘  └──────────┘  └─────────────────────┘ │
│       │            │                    │            │
│  ┌────┴────┐  ┌────┴─────┐     ┌───────┴──────┐    │
│  │ Schemas │  │ LLM/RAG  │     │ SQLite/MySQL │    │
│  │(Pydantic)│  │ (litellm)│     │   + PDFs     │    │
│  └─────────┘  └──────────┘     └──────────────┘    │
├──────────────────────────────────────────────────────┤
│              Collectors & Enrichment                 │
│    arXiv · Semantic Scholar · OpenReview · ACL       │
└──────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+ with [uv](https://docs.astral.sh/uv/)
- Node.js 18+
- An LLM API key (any provider supported by [litellm](https://docs.litellm.ai/))

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/PolarSnowLeopard/PaperRader.git
cd PaperRader

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker compose up -d

# Access at http://localhost:3000
```

### Option 2: Manual Setup

```bash
git clone https://github.com/PolarSnowLeopard/PaperRader.git
cd PaperRader

# Backend
uv sync
cp .env.example .env   # Edit with your API keys
uv run paperader init-db
uv run paperader serve  # API at http://localhost:8001

# Frontend (in a new terminal)
cd frontend
npm install
npm run dev             # UI at http://localhost:5173
```

## Project Structure

```
PaperRader/
├── paperader/                 # Core Python package
│   ├── collectors/            #   Paper sources (arXiv, S2, OpenReview, ACL)
│   ├── llm/                   #   LLM client & prompt templates
│   ├── models/                #   SQLAlchemy ORM models
│   ├── search/                #   Smart search (intent → filter → rank)
│   ├── services/              #   Business logic (import, chunk, report, chat)
│   └── config.py              #   Settings via pydantic-settings
├── server/                    # FastAPI application
│   ├── routers/               #   API endpoints
│   └── schemas/               #   Pydantic request/response models
├── frontend/                  # Vue 3 + Vite SPA
│   └── src/
│       ├── api/               #   Axios API clients
│       ├── views/             #   Page components
│       └── styles/            #   Global CSS design system
├── scripts/                   # Operational scripts
├── docker-compose.yml         # Container orchestration
├── Dockerfile                 # Backend image
└── pyproject.toml             # Python project config
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic |
| **Frontend** | Vue 3, Vite, Ant Design Vue, md-editor-v3 |
| **LLM** | litellm (OpenAI, Gemini, Claude, etc.) |
| **Database** | SQLite (dev) / MySQL (prod) |
| **PDF Processing** | PyMuPDF (text extraction & chunking) |
| **Data Sources** | arXiv API, Semantic Scholar, OpenReview, ACL Anthology, CrossRef |
| **Deployment** | Docker Compose, GitHub Actions, Nginx |

## Roadmap

PaperRader is more than a paper management tool — it's evolving into a research toolkit:

- [ ] Advanced PDF annotation and highlighting
- [ ] Citation graph visualization
- [ ] Paper recommendation engine
- [ ] Standalone CLI tools for paper collection and analysis
- [ ] Pluggable skills system for custom research workflows
- [ ] Browser extension for one-click paper capture
- [ ] Multi-user collaboration with shared workspaces

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built with coffee and curiosity for the research community.</sub>
</div>

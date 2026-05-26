# PaperRader

AI-powered research paper assistant for collecting, searching, and analyzing academic papers.

## Quick Start

```bash
# Install dependencies (uses uv)
uv sync

# Set up environment
cp .env.example .env  # Edit with your API keys

# Initialize database
uv run paperader init-db

# Add subscriptions
uv run paperader subscribe --category cs.CL --category cs.AI

# Collect papers
uv run paperader collect --source arxiv

# Search
uv run paperader search "attention mechanism"
uv run paperader smart-search "LLM agent papers from NeurIPS"

# Start web server
uv run paperader serve
```

## Architecture

- **paperader/** — Core Python package (models, collectors, search, LLM, services)
- **server/** — FastAPI web application
- **frontend/** — Vue 3 + Vite + Ant Design Vue frontend
- **scripts/** — Standalone operational scripts

## Tech Stack

- Python 3.11+ (managed via uv), FastAPI, SQLAlchemy 2.0, Alembic
- SQLite (dev) / MySQL (prod via Tencent Cloud)
- litellm for LLM API calls
- Typer for CLI
- Vue 3 + Vite + Ant Design Vue for frontend

## Key Commands

```bash
uv run paperader init-db              # Create/migrate database
uv run paperader collect              # Run paper collection
uv run paperader collect --source dblp  # Collect from DBLP
uv run paperader subscribe            # Manage topic subscriptions
uv run paperader search "query"       # Keyword search
uv run paperader smart-search "query" # LLM semantic search
uv run paperader enrich               # Enrich with Semantic Scholar data
uv run paperader stats                # Show statistics
uv run paperader serve                # Start FastAPI server
```

## Database

Uses SQLAlchemy with Alembic migrations. Models in `paperader/models/`.
SQLite locally at `data/paperader.db`, MySQL in production.

Run migrations: `uv run alembic upgrade head`

## Environment Variables

Prefix: `PAPERADER_`. See `.env.example` for all options.

## Frontend Development

```bash
cd frontend
npm install
npm run dev    # Dev server at http://localhost:5173
```

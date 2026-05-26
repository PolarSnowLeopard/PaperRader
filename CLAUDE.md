# PaperRader

AI-powered research paper assistant for collecting, searching, and analyzing academic papers.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Set up environment
cp .env.example .env  # Edit with your API keys

# Initialize database
paperader init-db

# Add subscriptions
paperader subscribe --category cs.CL --category cs.AI

# Collect papers
paperader collect --source arxiv

# Search
paperader search "attention mechanism"
```

## Architecture

- **paperader/** — Core Python package (models, collectors, search, LLM, services)
- **server/** — FastAPI web application
- **frontend/** — Vue 3 + Vite frontend (Phase 3)
- **scripts/** — Standalone operational scripts

## Tech Stack

- Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic
- SQLite (dev) / MySQL (prod via Tencent Cloud)
- litellm for LLM API calls
- Typer for CLI

## Key Commands

```bash
paperader init-db          # Create/migrate database
paperader collect          # Run paper collection
paperader subscribe        # Manage topic subscriptions
paperader search "query"   # Search papers
paperader serve            # Start FastAPI server
```

## Database

Uses SQLAlchemy with Alembic migrations. Models in `paperader/models/`.
SQLite locally at `data/paperader.db`, MySQL in production.

## Environment Variables

Prefix: `PAPERADER_`. See `.env.example` for all options.

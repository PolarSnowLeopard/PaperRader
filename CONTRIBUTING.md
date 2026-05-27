# Contributing to PaperRader

Thank you for considering contributing to PaperRader! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
   ```bash
   git clone https://github.com/YOUR_USERNAME/PaperRader.git
   cd PaperRader
   ```
3. **Create a branch** for your feature or fix
   ```bash
   git checkout -b feat/my-feature
   ```
4. **Set up the development environment** — see the [README](README.md#quick-start) for instructions

## Development Workflow

### Backend (Python)

```bash
# Install dependencies
uv sync

# Run the server in development mode
uv run uvicorn server.main:app --reload --port 8001

# Lint
uv run ruff check .
uv run ruff format .
```

### Frontend (Vue 3)

```bash
cd frontend
npm install
npm run dev     # Dev server at http://localhost:5173
npm run build   # Production build
```

## Code Style

- **Python**: We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Configuration is in `pyproject.toml`.
- **JavaScript/Vue**: Follow the existing patterns in the codebase. Use Composition API with `<script setup>`.

## Commit Messages

We follow a simplified [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>

[optional body]
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation changes
- `refactor` — Code refactoring (no feature change)
- `style` — UI/CSS changes
- `chore` — Build, CI, dependency updates

**Examples:**
```
feat: add batch PDF download for workspace
fix: resolve upload failure with non-ASCII filenames
docs: add deployment guide for Docker Compose
```

## Pull Requests

1. Keep PRs focused — one feature or fix per PR
2. Update documentation if your change affects user-facing behavior
3. Make sure the project builds without errors:
   ```bash
   cd frontend && npm run build
   ```
4. Write a clear PR description explaining **what** and **why**

## Reporting Issues

- Use [GitHub Issues](https://github.com/PolarSnowLeopard/PaperRader/issues)
- Include steps to reproduce, expected vs actual behavior
- Mention your OS, Python version, and browser if relevant

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

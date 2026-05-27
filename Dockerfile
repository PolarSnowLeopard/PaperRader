FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY paperader/ paperader/
COPY server/ server/
COPY scripts/ scripts/
COPY alembic/ alembic/
COPY alembic.ini .

RUN uv sync --frozen --no-dev

RUN mkdir -p data

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8001"]

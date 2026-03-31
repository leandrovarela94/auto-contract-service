# ── Stage 1: dependências com uv ─────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: imagem final ──────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY main.py config.py ./
COPY adapters/ ./adapters/
COPY models/ ./models/
COPY routes/ ./routes/
COPY services/ ./services/
COPY static/ ./static/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    OLLAMA_BASE_URL=http://ollama:11434 \
    OLLAMA_MODEL=llama3.3

EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

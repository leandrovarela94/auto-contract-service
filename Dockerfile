# ── Stage 1: dependências com uv ─────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

WORKDIR /app

# Copia arquivos de lock antes do código (melhor cache de camadas)
COPY pyproject.toml uv.lock ./

# Instala dependências no diretório /app/.venv sem tocar no sistema
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: imagem final enxuta ──────────────────────────────────────────────
FROM python:3.12-alpine AS runtime

WORKDIR /app

# Copia o virtualenv pronto do builder
COPY --from=builder /app/.venv /app/.venv

# Copia apenas o necessário
COPY main.py config.py ./
COPY static/ ./static/

# Usa o Python do venv diretamente (sem ativar)
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

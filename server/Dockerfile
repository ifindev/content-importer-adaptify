FROM python:3.12-slim AS dev

# Standalone uv binary, no pip install needed.
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONUNBUFFERED=1

COPY . .
RUN uv sync --locked

EXPOSE 8000
CMD ["uv", "run", "fastapi", "dev", "app/api/main.py", "--host", "0.0.0.0", "--port", "8000"]

# TODO(Phase 5): FROM python:3.12-slim AS prod
#   uv sync --locked --no-dev --no-editable, then run without --reload

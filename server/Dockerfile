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

FROM python:3.12-slim AS prod

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1

# Dependencies first so this layer stays cached when only app code changes.
COPY pyproject.toml uv.lock ./
# uv is mounted for the build only, so it isn't shipped in the image.
RUN --mount=from=ghcr.io/astral-sh/uv:0.11,source=/uv,target=/bin/uv \
    uv sync --locked --no-dev --no-install-project
COPY README.md ./
COPY app ./app
RUN --mount=from=ghcr.io/astral-sh/uv:0.11,source=/uv,target=/bin/uv \
    uv sync --locked --no-dev --no-editable

RUN useradd --system --no-create-home app
USER app

# sh -c so $PORT expands; exec so uvicorn is PID 1 and gets SIGTERM.
CMD ["sh", "-c", "exec fastapi run app/api/main.py --host 0.0.0.0 --port ${PORT:-8080}"]

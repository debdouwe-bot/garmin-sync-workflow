# syntax=docker/dockerfile:1
FROM python:3.14-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.17 /uv /uvx /bin/
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV UV_PYTHON_PREFERENCE=only-system \
    UV_NO_PYTHON_DOWNLOADS=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_COMPILE_BYTECODE_TIMEOUT=900
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

FROM python:3.14-slim AS runtime
WORKDIR /app
ENV UV_PYTHON_PREFERENCE=only-system \
    UV_NO_PYTHON_DOWNLOADS=1 \
    HOME=/tmp \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:${PATH}"
COPY --from=build /app /app
USER 1000:1000
CMD ["python", "-m", "worker.entrypoints.worker"]

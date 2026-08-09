# --- Stage 1: install dependencies with uv -----------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Dependency layer first: reused from cache unless the lockfile changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --- Stage 2: runtime — no uv, no build tools ---------------------------------
FROM python:3.12-slim-bookworm

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH" \
    MCP_TRANSPORT=http

RUN useradd --create-home appuser
USER appuser

EXPOSE 8080
CMD ["mydata-mcp"]

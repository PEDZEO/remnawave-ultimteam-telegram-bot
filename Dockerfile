FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.10.8 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-dev

FROM python:3.13-slim

ARG VERSION="v3.26.0" # x-release-please-version
ARG BUILD_DATE
ARG VCS_REF

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN groupadd -g 1000 app && \
    useradd -u 1000 -g 1000 -m -s /bin/bash app

WORKDIR /app

COPY --chown=app:app . .

RUN mkdir -p logs data uploads && chown app:app logs data uploads

USER app

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VERSION=${VERSION} \
    BUILD_DATE=${BUILD_DATE} \
    VCS_REF=${VCS_REF}

EXPOSE 8080

LABEL org.opencontainers.image.title="Remnawave Ultimteam Telegram Bot" \
      org.opencontainers.image.description="Ultimteam VPN bot and cabinet backend for Remnawave" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot" \
      org.opencontainers.image.url="https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot" \
      org.opencontainers.image.vendor="PEDZEO"

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["python", "main.py"]

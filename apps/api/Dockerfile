FROM python:3.11-alpine3.22 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk add --no-cache \
    build-base \
    postgresql-dev \
    so:libfontconfig.so.1 \
    so:libgobject-2.0.so.0 \
    so:libharfbuzz.so.0 \
    so:libharfbuzz-subset.so.0 \
    so:libpango-1.0.so.0 \
    so:libpangoft2-1.0.so.0

# Explicit whitelist — .dockerignore is defense-in-depth, not the only barrier
COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY alembic ./alembic

# Editable install so the package always resolves to /app source
# (prod: the COPYed source; dev: the compose bind-mount masking it).
# Prod deps only — [ai] ships the lazily-imported LLM SDKs, no [dev] tools.
RUN python -m venv /opt/venv && \
    /opt/venv/bin/python -m pip install --no-cache-dir --upgrade pip setuptools wheel jaraco.context && \
    /opt/venv/bin/pip install --no-cache-dir -e ".[ai,observability,rag]" && \
    /opt/venv/bin/python -m pip install --no-cache-dir --upgrade wheel jaraco.context

FROM python:3.11-alpine3.22

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    XDG_CACHE_HOME="/app/.cache"

WORKDIR /app

RUN apk add --no-cache \
    font-noto \
    font-noto-devanagari \
    font-noto-telugu \
    libpq \
    so:libfontconfig.so.1 \
    so:libgobject-2.0.so.0 \
    so:libharfbuzz.so.0 \
    so:libharfbuzz-subset.so.0 \
    so:libpango-1.0.so.0 \
    so:libpangoft2-1.0.so.0 && \
    python -m pip install --no-cache-dir --upgrade pip setuptools wheel jaraco.context && \
    adduser -D -H -s /sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

# Explicit whitelist — .dockerignore is defense-in-depth, not the only barrier
COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY alembic ./alembic

# Local-disk upload storage must be writable by the runtime user
RUN mkdir -p /app/.cache /app/uploads && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status==200 else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

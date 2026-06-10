# Pin by digest before production deploys:
#   docker pull python:3.11-slim
#   docker inspect --format='{{index .RepoDigests 0}}' python:3.11-slim
# then replace the tag below with python:3.11-slim@sha256:<digest>
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin appuser

# Explicit whitelist — .dockerignore is defense-in-depth, not the only barrier
COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY alembic ./alembic

# Editable install so the package always resolves to /app source
# (prod: the COPYed source; dev: the compose bind-mount masking it).
# Prod deps only — [ai] ships the lazily-imported LLM SDKs, no [dev] tools.
RUN pip install --no-cache-dir -e ".[ai]"

# Local-disk upload storage must be writable by the runtime user
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status==200 else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

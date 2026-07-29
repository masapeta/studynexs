"""Operational Proof static checks for production-like runtime files."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROD_COMPOSE = REPO_ROOT / "infra" / "docker" / "docker-compose.prod.yml"
PROMETHEUS_PROD = REPO_ROOT / "infra" / "observability" / "prometheus.prod.yml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_prod_compose_exists_and_keeps_runtime_services_private():
    text = PROD_COMPOSE.read_text(encoding="utf-8")

    assert "ENVIRONMENT: production" in text
    assert "container_name: studynexs-prod-api" in text
    assert "container_name: studynexs-prod-worker" in text
    assert "../../apps/api:/app" not in text
    assert '"8000:8000"' not in text
    assert '"5432:5432"' not in text
    assert '"6379:6379"' not in text
    assert '"6333:6333"' not in text
    assert (
        "${STUDYNEXS_UPLOADS_DIR:-../../ops-artifacts/operational-proof/uploads}:/app/uploads"
        in text
    )
    assert '"${STUDYNEXS_NGINX_BIND:-127.0.0.1}:${STUDYNEXS_NGINX_PORT:-8080}:80"' in text


def test_prod_compose_uses_synthetic_proof_settings_without_real_secret_files():
    text = PROD_COMPOSE.read_text(encoding="utf-8")

    assert "AI_DEFAULT_PROVIDER: ollama" in text
    assert "METRICS_TOKEN: ${METRICS_TOKEN:-studynexs-local-operational-proof-token}" in text
    assert "../observability/prometheus.prod.yml:/etc/prometheus/prometheus.yml:ro" in text
    assert "/etc/prometheus/secrets/metrics_token:ro" in text
    assert "env_file:" not in text
    assert ".env" not in text


def test_prod_prometheus_uses_metrics_token_file():
    text = PROMETHEUS_PROD.read_text(encoding="utf-8")

    assert "metrics_path: /metrics" in text
    assert "authorization:" in text
    assert "credentials_file: /etc/prometheus/secrets/metrics_token" in text


def test_ci_runs_on_develop_branch():
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "branches: [phase-0-foundation, main, develop]" in text

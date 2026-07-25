"""Platform observability metrics for HTTP and background jobs."""
from __future__ import annotations

from app.core.platform_metrics import PlatformMetricsRegistry


def test_platform_metrics_prometheus_text_includes_http_and_job_metrics():
    registry = PlatformMetricsRegistry()
    registry.record_http_request(
        method="GET",
        path="/api/v1/exams/{id}",
        status_code=200,
        duration_ms=125,
    )
    registry.record_job_event(task="answer_sheet_eval", status="done", duration_ms=250)

    text = registry.prometheus_text()

    assert "studynexs_http_requests_total" in text
    assert 'path="/api/v1/exams/{id}"' in text
    assert 'status_class="2xx"' in text
    assert "studynexs_http_request_duration_seconds_bucket" in text
    assert "studynexs_jobs_total" in text
    assert 'task="answer_sheet_eval"' in text
    assert "studynexs_job_duration_seconds_bucket" in text


def test_platform_metrics_snapshot_groups_statuses():
    registry = PlatformMetricsRegistry()
    registry.record_http_request(method="POST", path="/x", status_code=201, duration_ms=10)
    registry.record_http_request(method="POST", path="/x", status_code=409, duration_ms=20)
    registry.record_job_event(task="answer_sheet_eval", status="running")

    snap = registry.snapshot()

    assert snap["http_requests_total"] == 2
    assert snap["http_by_status_class"]["2xx"] == 1
    assert snap["http_by_status_class"]["4xx"] == 1
    assert snap["jobs_by_status"]["running"] == 1

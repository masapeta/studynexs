"""H7 production operations check helpers."""

from __future__ import annotations

from scripts.production_ops_check import check_metrics, check_metrics_auth, parse_prometheus_samples


def test_parse_prometheus_samples_with_labels_and_values():
    text = """
    # HELP studynexs_job_status_current Current queued/running/failed jobs
    studynexs_job_status_current{task="answer_sheet_eval",status="queued"} 2
    studynexs_job_status_scrape_error 0
    """

    samples = parse_prometheus_samples(text)

    assert samples == [
        {
            "name": "studynexs_job_status_current",
            "labels": {"task": "answer_sheet_eval", "status": "queued"},
            "value": 2.0,
        },
        {
            "name": "studynexs_job_status_scrape_error",
            "labels": {},
            "value": 0.0,
        },
    ]


def test_check_metrics_fails_stale_backlog(monkeypatch):
    text = """
    studynexs_job_status_scrape_error 0
    studynexs_job_status_current{task="answer_sheet_eval",status="queued"} 1
    studynexs_job_status_oldest_age_seconds{task="answer_sheet_eval",status="queued"} 3600
    """

    monkeypatch.setattr(
        "scripts.production_ops_check._http_text",
        lambda *_args, **_kwargs: (text, None),
    )

    result = check_metrics("http://test", max_job_age_seconds=1800)

    assert result.status == "fail"
    assert "stale job backlog" in result.detail


def test_check_metrics_passes_without_failed_or_stale_jobs(monkeypatch):
    text = """
    studynexs_job_status_scrape_error 0
    studynexs_job_status_current{task="answer_sheet_eval",status="queued"} 1
    studynexs_job_status_oldest_age_seconds{task="answer_sheet_eval",status="queued"} 60
    """

    monkeypatch.setattr(
        "scripts.production_ops_check._http_text",
        lambda *_args, **_kwargs: (text, None),
    )

    result = check_metrics("http://test", max_job_age_seconds=1800)

    assert result.status == "pass"


def test_check_metrics_auth_requires_401_then_authenticated_success(monkeypatch):
    text = """
    studynexs_job_status_scrape_error 0
    studynexs_job_status_current{task="answer_sheet_eval",status="queued"} 0
    """

    calls: list[dict[str, str] | None] = []

    def fake_http_text(_url, **kwargs):
        headers = kwargs.get("headers")
        calls.append(headers)
        if headers:
            return text, None
        return None, "HTTP Error 401: Unauthorized"

    monkeypatch.setattr("scripts.production_ops_check._http_text", fake_http_text)

    result = check_metrics_auth(
        "http://test",
        token="ops-token",
        max_job_age_seconds=1800,
    )

    assert result.status == "pass"
    assert calls == [None, {"Authorization": "Bearer ops-token"}]

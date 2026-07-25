"""Platform observability metrics for HTTP and background job operations.

This complements the AI telemetry registry. Keep labels deliberately low-cardinality:
routes are normalized before recording, job labels use the registered task name, and
status labels are bounded values.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class _Histogram:
    buckets: tuple[float, ...] = (50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000, 60000)
    counts: dict[float, int] = field(default_factory=lambda: defaultdict(int))
    total: int = 0
    sum_ms: float = 0.0

    def observe(self, value_ms: float) -> None:
        self.total += 1
        self.sum_ms += value_ms
        for bound in self.buckets:
            if value_ms <= bound:
                self.counts[bound] += 1

    def prometheus_lines(self, name: str, labels: str) -> list[str]:
        lines: list[str] = []
        cumulative = 0
        for bound in self.buckets:
            cumulative += self.counts[bound]
            lines.append(f'{name}_bucket{{{labels},le="{bound / 1000.0:g}"}} {cumulative}')
        lines.append(f'{name}_bucket{{{labels},le="+Inf"}} {self.total}')
        lines.append(f"{name}_sum{{{labels}}} {self.sum_ms / 1000.0}")
        lines.append(f"{name}_count{{{labels}}} {self.total}")
        return lines


class PlatformMetricsRegistry:
    """Thread-safe in-process counters/histograms for core platform operations."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._http_requests: dict[tuple[str, str, str], int] = defaultdict(int)
        self._http_latency: dict[tuple[str, str, str], _Histogram] = defaultdict(_Histogram)
        self._job_events: dict[tuple[str, str], int] = defaultdict(int)
        self._job_latency: dict[tuple[str, str], _Histogram] = defaultdict(_Histogram)

    @staticmethod
    def _status_class(status_code: int) -> str:
        if status_code < 100:
            return "unknown"
        return f"{status_code // 100}xx"

    def record_http_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        status_class = self._status_class(status_code)
        key = (method.upper(), path or "unknown", status_class)
        with self._lock:
            self._http_requests[key] += 1
            if duration_ms >= 0:
                self._http_latency[key].observe(duration_ms)

    def record_job_event(
        self,
        *,
        task: str,
        status: str,
        duration_ms: float | None = None,
    ) -> None:
        key = (task or "unknown", status or "unknown")
        with self._lock:
            self._job_events[key] += 1
            if duration_ms is not None and duration_ms >= 0:
                self._job_latency[key].observe(duration_ms)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "uptime_seconds": round(time.time() - self._started_at, 1),
                "http_requests_total": sum(self._http_requests.values()),
                "job_events_total": sum(self._job_events.values()),
                "http_by_status_class": _group_counts(self._http_requests, index=2),
                "jobs_by_status": _group_counts(self._job_events, index=1),
            }

    def prometheus_text(self) -> str:
        lines = [
            "# HELP studynexs_platform_uptime_seconds Process uptime for this StudyNexs process",
            "# TYPE studynexs_platform_uptime_seconds gauge",
            f"studynexs_platform_uptime_seconds {time.time() - self._started_at:.3f}",
            "",
            "# HELP studynexs_http_requests_total HTTP requests by method/path/status class",
            "# TYPE studynexs_http_requests_total counter",
        ]
        with self._lock:
            for (method, path, status_class), count in sorted(self._http_requests.items()):
                labels = (
                    f'method="{_esc(method)}",path="{_esc(path)}",'
                    f'status_class="{_esc(status_class)}"'
                )
                lines.append(f"studynexs_http_requests_total{{{labels}}} {count}")

            lines.extend([
                "",
                "# HELP studynexs_http_request_duration_seconds HTTP request duration",
                "# TYPE studynexs_http_request_duration_seconds histogram",
            ])
            for (method, path, status_class), hist in sorted(self._http_latency.items()):
                labels = (
                    f'method="{_esc(method)}",path="{_esc(path)}",'
                    f'status_class="{_esc(status_class)}"'
                )
                lines.extend(
                    hist.prometheus_lines("studynexs_http_request_duration_seconds", labels)
                )

            lines.extend([
                "",
                "# HELP studynexs_jobs_total Background job lifecycle events by task/status",
                "# TYPE studynexs_jobs_total counter",
            ])
            for (task, status), count in sorted(self._job_events.items()):
                labels = f'task="{_esc(task)}",status="{_esc(status)}"'
                lines.append(f"studynexs_jobs_total{{{labels}}} {count}")

            lines.extend([
                "",
                "# HELP studynexs_job_duration_seconds Background job duration",
                "# TYPE studynexs_job_duration_seconds histogram",
            ])
            for (task, status), hist in sorted(self._job_latency.items()):
                labels = f'task="{_esc(task)}",status="{_esc(status)}"'
                lines.extend(hist.prometheus_lines("studynexs_job_duration_seconds", labels))

        return "\n".join(lines) + "\n"


def _group_counts(data: dict[tuple[str, ...], int], *, index: int) -> dict[str, int]:
    grouped: dict[str, int] = defaultdict(int)
    for key, value in data.items():
        grouped[key[index]] += value
    return dict(grouped)


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


platform_metrics = PlatformMetricsRegistry()


async def job_status_prometheus_text() -> str:
    """Current actionable job counts from the database for queue/backlog alerting.

    The in-process registry records lifecycle events for whichever process is scraped.
    This DB-backed gauge complements it with API-visible queued/running/failed counts so
    operators can alert on stalled workers or growing backlogs from the normal scrape target.
    """
    from sqlalchemy import func, select

    from app.core.database import async_session_factory
    from app.db.models.job import Job, JobStatus

    lines = [
        "# HELP studynexs_job_status_current Current queued/running/failed jobs by task/status",
        "# TYPE studynexs_job_status_current gauge",
    ]
    try:
        async with async_session_factory() as session:
            rows = (
                await session.execute(
                    select(Job.type, Job.status, func.count(), func.min(Job.created_at))
                    .where(Job.status.in_([JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.FAILED]))
                    .group_by(Job.type, Job.status)
                )
            ).all()
        now = datetime.now(timezone.utc)
        age_lines = [
            "",
            "# HELP studynexs_job_status_oldest_age_seconds Oldest job age by task/status",
            "# TYPE studynexs_job_status_oldest_age_seconds gauge",
        ]
        for task, status, count, oldest_created_at in rows:
            status_label = status.value if hasattr(status, "value") else str(status)
            labels = f'task="{_esc(task)}",status="{_esc(status_label)}"'
            lines.append(
                f"studynexs_job_status_current{{{labels}}} {int(count)}"
            )
            if oldest_created_at:
                if oldest_created_at.tzinfo is None:
                    oldest_created_at = oldest_created_at.replace(tzinfo=timezone.utc)
                age_seconds = max(0.0, (now - oldest_created_at).total_seconds())
                age_lines.append(
                    f"studynexs_job_status_oldest_age_seconds{{{labels}}} {age_seconds:.3f}"
                )
        lines.extend(age_lines)
        lines.extend([
            "",
            "# HELP studynexs_job_status_scrape_error Job status scrape failures",
            "# TYPE studynexs_job_status_scrape_error gauge",
            "studynexs_job_status_scrape_error 0",
        ])
    except Exception:
        lines.extend([
            "",
            "# HELP studynexs_job_status_scrape_error Job status scrape failures",
            "# TYPE studynexs_job_status_scrape_error gauge",
            "studynexs_job_status_scrape_error 1",
        ])
    return "\n".join(lines) + "\n"

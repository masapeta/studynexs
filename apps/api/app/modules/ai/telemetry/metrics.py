"""In-process AI metrics — Prometheus text exposition for scraping and scaling alerts."""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field


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
            lines.append(
                f'{name}_bucket{{{labels},le="{bound}"}} {cumulative}'
            )
        lines.append(f'{name}_bucket{{{labels},le="+Inf"}} {self.total}')
        lines.append(f"{name}_sum{{{labels}}} {self.sum_ms / 1000.0}")
        lines.append(f"{name}_count{{{labels}}} {self.total}")
        return lines


class AIMetricsRegistry:
    """Thread-safe counters/histograms for LLM and AI-adjacent calls."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._requests: dict[tuple[str, ...], int] = defaultdict(int)
        self._tokens_in: dict[tuple[str, ...], int] = defaultdict(int)
        self._tokens_out: dict[tuple[str, ...], int] = defaultdict(int)
        self._latency: dict[tuple[str, ...], _Histogram] = defaultdict(_Histogram)
        self._failures: dict[tuple[str, ...], int] = defaultdict(int)
        self._fallbacks: dict[tuple[str, ...], int] = defaultdict(int)

    def _key(
        self,
        *,
        feature: str,
        provider: str,
        model: str,
        status: str,
    ) -> tuple[str, str, str, str]:
        return (feature or "unknown", provider or "unknown", model or "unknown", status)

    def record_llm_call(
        self,
        *,
        feature: str,
        provider: str,
        model: str,
        status: str,
        latency_ms: int = 0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        used_fallback: bool = False,
    ) -> None:
        key = self._key(feature=feature, provider=provider, model=model, status=status)
        with self._lock:
            self._requests[key] += 1
            self._tokens_in[key] += tokens_in
            self._tokens_out[key] += tokens_out
            if latency_ms > 0:
                self._latency[key].observe(float(latency_ms))
            if status == "error":
                self._failures[key] += 1
            if used_fallback:
                fb_key = (feature or "unknown", provider or "unknown", model or "unknown")
                self._fallbacks[fb_key] += 1

    def snapshot(self) -> dict:
        """JSON-friendly summary for admin dashboards."""
        with self._lock:
            total_requests = sum(self._requests.values())
            total_errors = sum(self._failures.values())
            total_fallbacks = sum(self._fallbacks.values())
            by_feature: dict[str, int] = defaultdict(int)
            by_provider: dict[str, int] = defaultdict(int)
            for (feature, provider, _model, status), count in self._requests.items():
                if status != "error":
                    by_feature[feature] += count
                    by_provider[provider] += count
            return {
                "uptime_seconds": round(time.time() - self._started_at, 1),
                "llm_requests_total": total_requests,
                "llm_errors_total": total_errors,
                "llm_fallback_success_total": total_fallbacks,
                "by_feature": dict(by_feature),
                "by_provider": dict(by_provider),
            }

    def prometheus_text(self) -> str:
        lines = [
            "# HELP studynexs_ai_llm_requests_total LLM calls by feature/provider/model/status",
            "# TYPE studynexs_ai_llm_requests_total counter",
        ]
        with self._lock:
            for (feature, provider, model, status), count in sorted(self._requests.items()):
                labels = (
                    f'feature="{feature}",provider="{provider}",'
                    f'model="{_esc(model)}",status="{status}"'
                )
                lines.append(f"studynexs_ai_llm_requests_total{{{labels}}} {count}")

            lines.extend([
                "",
                "# HELP studynexs_ai_llm_tokens_in_total Input tokens consumed",
                "# TYPE studynexs_ai_llm_tokens_in_total counter",
            ])
            for (feature, provider, model, status), total in sorted(self._tokens_in.items()):
                labels = (
                    f'feature="{feature}",provider="{provider}",'
                    f'model="{_esc(model)}",status="{status}"'
                )
                lines.append(f"studynexs_ai_llm_tokens_in_total{{{labels}}} {total}")

            lines.extend([
                "",
                "# HELP studynexs_ai_llm_tokens_out_total Output tokens generated",
                "# TYPE studynexs_ai_llm_tokens_out_total counter",
            ])
            for (feature, provider, model, status), total in sorted(self._tokens_out.items()):
                labels = (
                    f'feature="{feature}",provider="{provider}",'
                    f'model="{_esc(model)}",status="{status}"'
                )
                lines.append(f"studynexs_ai_llm_tokens_out_total{{{labels}}} {total}")

            lines.extend([
                "",
                "# HELP studynexs_ai_llm_latency_seconds LLM call latency",
                "# TYPE studynexs_ai_llm_latency_seconds histogram",
            ])
            for key, hist in sorted(self._latency.items()):
                feature, provider, model, status = key
                labels = (
                    f'feature="{feature}",provider="{provider}",'
                    f'model="{_esc(model)}",status="{status}"'
                )
                lines.extend(hist.prometheus_lines("studynexs_ai_llm_latency_seconds", labels))

            lines.extend([
                "",
                "# HELP studynexs_ai_llm_fallback_success_total Successful calls "
                "after primary failure",
                "# TYPE studynexs_ai_llm_fallback_success_total counter",
            ])
            for (feature, provider, model), count in sorted(self._fallbacks.items()):
                labels = f'feature="{feature}",provider="{provider}",model="{_esc(model)}"'
                lines.append(f"studynexs_ai_llm_fallback_success_total{{{labels}}} {count}")

        return "\n".join(lines) + "\n"


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


ai_metrics = AIMetricsRegistry()

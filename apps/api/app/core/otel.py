"""OpenTelemetry bootstrap — traces, metrics, and auto-instrumentation.

Disabled when OTEL_ENABLED=false or ENVIRONMENT=testing. Exports via OTLP to the
collector (see infra/observability/). Requires pip install -e ".[observability]".
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

    from app.core.config import Settings

_initialized = False


def otel_enabled(settings: Settings) -> bool:
    from app.core.config import Environment

    if settings.ENVIRONMENT == Environment.TESTING:
        return False
    if not settings.OTEL_ENABLED:
        return False
    return bool((settings.OTEL_EXPORTER_OTLP_ENDPOINT or "").strip())


def _otel_available() -> bool:
    try:
        import opentelemetry  # noqa: F401

        return True
    except ImportError:
        return False


def setup_opentelemetry(settings: Settings) -> None:
    """Configure global TracerProvider and MeterProvider."""
    global _initialized
    if _initialized or not otel_enabled(settings):
        return
    if not _otel_available():
        return

    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
    from opentelemetry.semconv.resource import ResourceAttributes

    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/")
    protocol = (settings.OTEL_EXPORTER_OTLP_PROTOCOL or "grpc").lower()

    if protocol in ("http", "http/protobuf"):
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter as HTTPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter as HTTPSpanExporter,
        )

        span_exporter = HTTPSpanExporter(endpoint=f"{endpoint}/v1/traces")
        metric_exporter = HTTPMetricExporter(endpoint=f"{endpoint}/v1/metrics")
    else:
        span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)

    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: settings.OTEL_SERVICE_NAME,
            ResourceAttributes.SERVICE_VERSION: settings.APP_VERSION,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT.value,
        }
    )
    sampler = ParentBasedTraceIdRatio(settings.OTEL_TRACES_SAMPLE_RATE)

    tracer_provider = TracerProvider(resource=resource, sampler=sampler)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=settings.OTEL_METRIC_EXPORT_INTERVAL_MS,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    HTTPXClientInstrumentor().instrument()
    _initialized = True


def instrument_fastapi(app: FastAPI, settings: Settings) -> None:
    if not otel_enabled(settings) or not _otel_available():
        return
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="/health,/ready,/metrics",
    )


def shutdown_opentelemetry() -> None:
    global _initialized
    if not _initialized or not _otel_available():
        return
    from opentelemetry import metrics, trace

    tracer_provider = trace.get_tracer_provider()
    if hasattr(tracer_provider, "shutdown"):
        tracer_provider.shutdown()
    meter_provider = metrics.get_meter_provider()
    if hasattr(meter_provider, "shutdown"):
        meter_provider.shutdown()
    _initialized = False


def get_tracer(name: str):
    from opentelemetry import trace

    return trace.get_tracer(name)


def get_meter(name: str):
    from opentelemetry import metrics

    return metrics.get_meter(name)


def current_trace_id() -> str | None:
    if not _otel_available():
        return None
    from opentelemetry import trace

    span = trace.get_current_span()
    ctx = span.get_span_context()
    if not ctx.is_valid:
        return None
    return format(ctx.trace_id, "032x")

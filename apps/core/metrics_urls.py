"""
Prometheus metrics endpoint.
"""

from django.http import HttpResponse
from django.urls import path
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram


# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)

# Database metrics
DB_CONNECTION_COUNT = Gauge(
    "database_connections_active",
    "Active database connections",
)


def metrics(request):
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


urlpatterns = [
    path("", metrics, name="metrics"),
]
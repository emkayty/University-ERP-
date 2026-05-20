"""
Health check URLs for K3s probes.
"""

from django.http import JsonResponse
from django.urls import path


def health_check(request):
    """Basic health check for K3s liveness probe."""
    return JsonResponse({"status": "healthy"})


def readiness_check(request):
    """Readiness check - checks database and Redis."""
    try:
        from django.db import connection
        connection.ensure_connection()
    except Exception:
        return JsonResponse(
            {"status": "unhealthy", "error": "database"},
            status=503,
        )
    
    return JsonResponse({"status": "ready"})


def liveness_check(request):
    """Liveness probe - checks if app is running."""
    return JsonResponse({"status": "alive"})


urlpatterns = [
    path("", health_check, name="health_check"),
    path("ready/", readiness_check, name="readiness_check"),
    path("live/", liveness_check, name="liveness_check"),
]
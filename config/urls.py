"""
URL Configuration for Nigerian University MIS.
Versioned API routing.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Root redirect
    path("", RedirectView.as_view(url="/api/v1/", permanent=False)),
    
    # Django Admin
    path("admin/", admin.site.urls),
    
    # API v1 - REST Framework
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.tenants.urls")),
    path("api/v1/core/", include("apps.core.urls")),
    path("api/v1/institutional/", include("apps.institutional.urls")),
    path("api/v1/admissions/", include("apps.admissions.urls")),
    path("api/v1/students/", include("apps.students.urls")),
    # path("api/v1/library/", include("apps.library.urls")),
    # path("api/v1/examinations/", include("apps.examinations.urls")),
    # path("api/v1/records/", include("apps.records.urls")),
    # path("api/v1/communications/", include("apps.communications.urls")),
    # path("api/v1/inventory/", include("apps.inventory.urls")),
    # path("api/v1/hostel/", include("apps.hostel.urls")),
    # path("api/v1/transport/", include("apps.transport.urls")),
    # path("api/v1/sports/", include("apps.sports.urls")),
    # path("api/v1/health/", include("apps.health.urls")),
    # path("api/v1/alumni/", include("apps.alumni.urls")),
    # path("api/v1/placement/", include("apps.placement.urls")),
    # path("api/v1/research/", include("apps.research.urls")),
    # path("api/v1/ict/", include("apps.ict.urls")),
    # path("api/v1/specialized/", include("apps.specialized.urls")),
    
    # API v1 - Django Ninja (ML inference)
    # path("api/ml/", include("apps.ml.urls")),
    
    # WebSocket
    path("ws/", include("config.wschannels.routing")),
    
    # Health check (no auth, used by K3s)
    path("health/", include("apps.core.health_urls")),
    
    # Prometheus metrics
    path("metrics/", include("apps.core.metrics_urls")),
]

# Debug toolbar in development
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
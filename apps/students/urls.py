"""
Student URLs.
Phase 1 Module 03.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.students import views

router = DefaultRouter()
router.register(r"", views.StudentViewSet)
router.register(r"documents", views.StudentDocumentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
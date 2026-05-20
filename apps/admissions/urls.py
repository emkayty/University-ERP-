"""
Admissions URLs.
Phase 1 Module 02.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.admissions import views

router = DefaultRouter()
router.register(r"applications", views.ApplicationViewSet)
router.register(r"offers", views.AdmissionOfferViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
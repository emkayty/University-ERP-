"""
Institutional URLs.
Phase 1 Module 01.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.institutional import views

router = DefaultRouter()
router.register(r"faculties", views.FacultyViewSet)
router.register(r"departments", views.DepartmentViewSet)
router.register(r"programmes", views.ProgrammeViewSet)
router.register(r"sessions", views.AcademicSessionViewSet)
router.register(r"semesters", views.SemesterViewSet)
router.register(r"grading", views.GradingConfigViewSet)
router.register(r"config", views.InstitutionalConfigViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
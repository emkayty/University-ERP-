"""
Examinations URLs.
Module 6 - Results workflow.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "examinations"

router = DefaultRouter()
router.register(r"batches", views.ResultBatchViewSet, basename="batch")
router.register(r"scores", views.ScoreViewSet, basename="score")
router.register(r"malpractice", views.MalpracticeCaseViewSet, basename="malpractice")

urlpatterns = router.urls
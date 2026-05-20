"""
Course Embedding Models for Semantic Search.
Phase 1 Module 07.
"""

from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import BaseModel


class CourseEmbedding(BaseModel):
    """Course semantic embedding storage."""
    course = models.OneToOneField(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="embedding",
    )
    embedding = models.JSONField(
        help_text="Vector embedding stored as JSON array",
    )
    embedded_at = models.DateTimeField(auto_now=True)
    model_version = models.CharField(
        max_length=50,
        default="sentence-transformers/all-MiniLM-L6-v2",
    )

    class Meta:
        db_table = "ml_course_embedding"
        verbose_name = "Course Embedding"
        verbose_name_plural = "Course Embeddings"

    def __str__(self) -> str:
        return f"Embedding for {self.course.code}"


class SearchLog(BaseModel):
    """Log of search queries for analytics."""
    query = models.CharField(max_length=500)
    results_count = models.IntegerField()
    execution_time_ms = models.IntegerField()
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    search_type = models.CharField(
        max_length=20,
        choices=[
            ("semantic", "Semantic"),
            ("fulltext", "Full-text"),
            ("hybrid", "Hybrid"),
        ],
    )

    class Meta:
        db_table = "ml_search_log"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Search: {self.query}"
"""
Face Verification Models.
Phase 4 - AI Domain 6.
"""

import uuid
from django.db import models

from apps.core.models import BaseModel


class StudentFaceEmbedding(BaseModel):
    """Student face embedding for verification."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="face_embeddings",
    )
    embedding = models.JSONField()  # 128-d FaceNet embedding
    captured_at = models.DateTimeField(auto_now_add=True)
    device_id = models.CharField(max_length=50, blank=True)
    quality_score = models.FloatField()
    consent_given = models.BooleanField(default=False)
    deletion_scheduled_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "ml_face_embedding"
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["deletion_scheduled_at"]),
        ]

    def __str__(self) -> str:
        return f"Face for {self.student.matric_number}"


class FaceVerificationLog(BaseModel):
    """Log of all verification attempts."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.SET_NULL,
        null=True,
    )
    verification_code = models.CharField(max_length=50)
    similarity_score = models.FloatField()
    passed = models.BooleanField()
    capture_time_ms = models.IntegerField()
    device_id = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Alert status
    alert_sent = models.BooleanField(default=False)
    alert_sent_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "ml_face_verification_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Verification {self.id} - {'PASS' if self.passed else 'FAIL'}"
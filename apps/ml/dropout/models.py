"""
Dropout Risk Models.
Phase 3 - AI Domain 1.
"""

from django.db import models

from apps.core.models import BaseModel


class StudentRiskScore(BaseModel):
    """Student dropout risk score."""
    RISK_LEVELS = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="risk_scores",
    )
    risk_score = models.FloatField()
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    model_version = models.CharField(max_length=50, default="1.0.0")
    feature_values = models.JSONField(default=dict)
    shap_explanation = models.JSONField(default=dict)
    scored_at = models.DateTimeField(auto_now_add=True)
    notified_advisor = models.BooleanField(default=False)

    class Meta:
        db_table = "ml_dropout_risk"
        ordering = ["-scored_at"]
        indexes = [
            models.Index(fields=["student", "-scored_at"]),
            models.Index(fields=["risk_level"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.matric_number}: {self.risk_score:.2f} ({self.risk_level})"
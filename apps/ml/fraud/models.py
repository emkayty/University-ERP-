"""
Fraud Detection Models.
Phase 2 - AI Domain 2.
"""

from django.db import models

from apps.core.models import BaseModel


class FraudFlag(BaseModel):
    """Fraud detection flag."""
    STATUS_CHOICES = [
        ("flagged", "Flagged"),
        ("reviewed", "Reviewed"),
        ("confirmed_fraud", "Confirmed Fraud"),
        ("false_positive", "False Positive"),
    ]

    payment = models.ForeignKey(
        "finance.Payment",
        on_delete=models.CASCADE,
        related_name="fraud_flags",
    )
    risk_score = models.FloatField()
    model_version = models.CharField(max_length=50, default="1.0.0")
    features_used = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="flagged",
    )
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_fraud_flags",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Auto-hold
    payment_held = models.BooleanField(default=False)

    class Meta:
        db_table = "ml_fraud_flag"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["risk_score"]),
        ]

    def __str__(self) -> str:
        return f"Fraud Flag {self.id} - Score: {self.risk_score:.2f}"
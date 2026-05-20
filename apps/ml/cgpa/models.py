"""
CGPA Forecasting.
Domain 1.2 - Academic Performance Prediction.
"""

from django.db import models
from apps.core.models import BaseModel


class CGPAPrediction(BaseModel):
    """Student CGPA prediction."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="cgpa_predictions",
    )
    session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
    )
    
    predicted_cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    confidence_score = models.PositiveSmallIntegerField(default=0)
    
    features = models.JSONField(default=dict)
    explanation = models.JSONField(default=dict)
    
    actual_cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    is_accurate = models.BooleanField(null=True)

    class Meta:
        db_table = "ml_cgpa_prediction"
        unique_together = [["student", "session"]]

    def __str__(self) -> str:
        return f"{self.student.matric_number}: {self.predicted_cgpa}"
"""
Admissions ML.
Domain D.5 - Predictive Admissions.
"""

from django.db import models
from apps.core.models import BaseModel


class AdmissionPrediction(BaseModel):
    """Predict admission success probability."""
    application = models.ForeignKey(
        "admissions.Application",
        on_delete=models.CASCADE,
        related_name="ml_predictions",
    )
    
    # Prediction
    probability = models.DecimalField(max_digits=4, decimal_places=2)  # 0-1 probability
    score = models.PositiveSmallIntegerField()  # Composite score
    
    # Features
    features = models.JSONField(default=dict)  # {"jamb_score": 250, "cgpa": 3.5, ...}
    
    # SHAP explanation
    explanation = models.JSONField(default=dict)
    
    # Outcome
    admitted = models.BooleanField(null=True)
    is_accurate = models.BooleanField(null=True)

    class Meta:
        db_table = "ml_admission_prediction"

    def __str__(self) -> str:
        return f"{self.application.id}: {self.probability}"


def predict_admission(application):
    """Predict admission success.
    
    Features: JAMB score, O-level grades, CGPA trend, program demand.
    """
    features = {}
    
    # JAMB score
    if application.jamb_score:
        features["jamb_score"] = float(application.jamb_score)
    
    # O-level aggregation
    if application.olevel_grades:
        features["olevel_avg"] = sum(application.olevel_grades) / len(application.olevel_grades)
    
    # Programme demand (historical)
    features["programme_demand"] = 1.0  # Placeholder
    
    # Simple scoring
    score = (
        features.get("jamb_score", 200) / 350 * 50 +  # JAMB weight
        features.get("olevel_avg", 3) * 10 +  # O-level weight
        features.get("programme_demand", 1) * 5
    )
    
    probability = min(score / 100, 1.0)
    
    return {
        "probability": round(probability, 2),
        "score": int(score),
        "features": features,
        "explanation": {
            "jamb": "Primary factor in admission decision",
            "olevel": "Secondary factor",
        }
    }
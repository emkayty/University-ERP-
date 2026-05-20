"""CGPA Forecasting Pipeline."""
from decimal import Decimal


def predict_cgpa(student, session):
    """Predict student CGPA for upcoming session.
    
    Uses features: attendance, fee payment, previous CGPA,
    first_gen status, course load.
    """
    # Placeholder for actual ML model
    # In production, load from MLflow
    
    features = {
        "previous_cgpa": float(student.current_cgpa) if student.current_cgpa else 2.0,
        "attendace_percent": 75.0,
        "fee_payment_rate": 0.9,
        "course_load": student.max_credit_load,
        "is_first_generation": student.is_first_generation,
    }
    
    # Simple linear model placeholder
    # CGPA prediction = weighted sum of features
    predicted = (
        features["previous_cgpa"] * 0.5 +
        features["attendace_percent"] / 100 * 0.2 +
        features["fee_payment_rate"] * 0.2 +
        features["course_load"] / 24 * 0.1
    )
    
    if features["is_first_generation"]:
        predicted *= 0.95  # Adjust for first-gen students
    
    return {
        "predicted_cgpa": round(min(max(predicted, 0.0), 4.0), 2),
        "confidence": 75,
        "features": features,
        "explanation": {
            "previous_cgpa": "Most important predictor",
            "attendance": "Second most important",
            "fee_payment": "Affected financial stress",
        }
    }


def calculate_accuracy(student_predictions):
    """Calculate accuracy of predictions vs actual results."""
    errors = []
    for pred in student_predictions:
        if pred.actual_cgpa:
            error = abs(float(pred.predicted_cgpa) - float(pred.actual_cgpa))
            errors.append(error)
            pred.is_accurate = error <= 0.5
            pred.save()
    
    if errors:
        return {
            "total": len(errors),
            "accurate": sum(1 for e in errors if e <= 0.5),
            "mse": sum(e * e for e in errors) / len(errors),
        }
    return None
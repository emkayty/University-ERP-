"""
Payment Fraud Detection.
Phase 2 - AI Domain 2.
"""

import logging
from dataclasses import dataclass

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class FraudScore:
    """Fraud detection result."""
    risk_score: float  # 0.0 to 1.0
    features: dict
    should_hold: bool


def get_student_payment_history(student_id: str) -> dict:
    """Get cached payment history for a student."""
    cache_key = f"student_payment_history_{student_id}"
    return cache.get(cache_key, {
        "count_24h": 0,
        "count_7d": 0,
        "mean_amount": 0,
        "total_7d": 0,
    })


def update_student_payment_history(student_id: str, amount: float):
    """Update student's payment history after successful payment."""
    cache_key = f"student_payment_history_{student_id}"
    history = get_student_payment_history(student_id)
    
    history["count_24h"] = history.get("count_24h", 0) + 1
    history["count_7d"] = history.get("count_7d", 0) + 1
    history["total_7d"] = history.get("total_7d", 0) + amount
    
    # Recalculate mean
    if history["count_7d"] > 0:
        history["mean_amount"] = history["total_7d"] / history["count_7d"]
    
    # Cache for 7 days
    from django.core.cache import cache
    cache.set(cache_key, history, 60 * 60 * 7)


def calculate_fraud_score(payment: "Payment") -> FraudScore:
    """
    Calculate fraud risk score using Isolation Forest concept.
    
    Features:
    - payment_amount
    - hour_of_day
    - payments_last_24h
    - payments_last_7d
    - amount_deviation_from_mean
    - gateway
    - payment_method
    """
    from django.utils import timezone
    from datetime import timedelta
    
    features = {}
    student = payment.invoice.student
    
    # Get payment history
    history = get_student_payment_history(str(student.id))
    
    # Feature 1: Amount deviation from student's mean
    mean_amount = history.get("mean_amount", 0)
    if mean_amount > 0:
        amount_ratio = float(payment.amount) / mean_amount
    else:
        amount_ratio = 1.0
    
    features["amount_ratio"] = amount_ratio
    
    # Feature 2: Unusual hour
    hour = payment.created_at.hour if payment.created_at else timezone.now().hour
    features["unusual_hour"] = hour < 6 or hour > 22
    
    # Feature 3: High frequency (24h)
    features["high_freq_24h"] = history.get("count_24h", 0) > 3
    
    # Feature 4: High frequency (7d)
    features["high_freq_7d"] = history.get("count_7d", 0) > 10
    
    # Feature 5: Large single payment
    features["large_payment"] = float(payment.amount) > 100000  # > 100k
    
    # Feature 6: New student (first payment)
    features["first_payment"] = history.get("count_7d", 0) == 0
    
    # Calculate risk score (simplified Isolation Forest concept)
    risk_score = 0.0
    
    if amount_ratio > 5:
        risk_score += 0.4
    elif amount_ratio > 2:
        risk_score += 0.2
    
    if features["unusual_hour"]:
        risk_score += 0.15
    
    if features["high_freq_24h"]:
        risk_score += 0.25
    
    if features["high_freq_7d"]:
        risk_score += 0.15
    
    if features["large_payment"]:
        risk_score += 0.2
    
    # Cap at 1.0
    risk_score = min(risk_score, 1.0)
    
    should_hold = risk_score > 0.85
    
    return FraudScore(
        risk_score=risk_score,
        features=features,
        should_hold=should_hold,
    )


def score_payment_task(payment_id: str) -> dict:
    """
    Celery task to score a payment for fraud.
    Called after payment verification.
    """
    from apps.finance.models import Payment
    from apps.ml.fraud.models import FraudFlag
    
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return {"status": "error", "message": "Payment not found"}
    
    # Calculate score
    result = calculate_fraud_score(payment)
    
    # Create fraud flag
    fraud_flag = FraudFlag.objects.create(
        payment=payment,
        risk_score=result.risk_score,
        model_version="1.0.0",
        features_used=result.features,
        status="flagged" if result.risk_score > 0.5 else "reviewed",
    )
    
    # Update payment history
    update_student_payment_history(
        str(payment.invoice.student.id),
        float(payment.amount),
    )
    
    # Auto-hold if high risk
    if result.should_hold:
        # Send alert to bursar
        logger.warning(
            f"High fraud risk detected: payment {payment_id}, "
            f"score {result.risk_score}"
        )
    
    return {
        "status": "success",
        "risk_score": result.risk_score,
        "flag_id": str(fraud_flag.id),
    }
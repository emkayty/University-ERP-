"""
Dropout Risk Celery Tasks.
Phase 3 - AI Domain 1.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="ml")
def score_all_students(tenant_id: str):
    """
    Score all active students for dropout risk.
    Weekly Celery Beat task: Sunday 2AM.
    """
    from apps.students.models import Student
    from apps.ml.dropout.models import StudentRiskScore
    from apps.ml.dropout.pipeline import (
        score_dropout_risk,
        check_ml_data_readiness,
    )
    
    # Check data readiness
    if not check_ml_data_readiness(tenant_id):
        logger.warning(f"ML data not ready for tenant {tenant_id}")
        return {"status": "not_ready"}
    
    students = Student.objects.filter(
        user__tenant_id=tenant_id,
        status="active",
    )
    
    scored = 0
    for student in students:
        try:
            risk_score, level, explanation = score_dropout_risk(str(student.id))
            
            StudentRiskScore.objects.create(
                student=student,
                risk_score=risk_score,
                risk_level=level,
                feature_values=explanation.get("features", {}),
                shap_explanation=explanation.get("top_factors", []),
            )
            
            # Notify advisor if critical
            if risk_score > 0.7:
                # Send notification to advisor
                pass
            
            scored += 1
            
        except Exception as e:
            logger.error(f"Scoring failed for {student.id}: {e}")
    
    return {"status": "success", "scored": scored}


@shared_task(bind=True, queue="ml")
def detect_malpractice_patterns(offering_id: str):
    """
    Detect exam malpractice patterns.
    Runs after exam score entry.
    """
    from apps.courses.models import CourseOffering
    from apps.examinations.models import Score, MalpracticePattern
    import numpy as np
    
    try:
        offering = CourseOffering.objects.get(id=offering_id)
    except CourseOffering.DoesNotExist:
        return {"status": "error", "message": "Offering not found"}
    
    scores = Score.objects.filter(offering=offering)
    
    if scores.count() < 10:
        # Too few to detect patterns
        return {"status": "skipped", "reason": "insufficient_data"}
    
    # 1. Check for grade distribution outliers (Z-score)
    total_scores = [float(s.total_score or 0) for s in scores]
    mean = np.mean(total_scores)
    std = np.std(total_scores)
    
    if std > 0:
        z_scores = [(s - mean) / std for s in total_scores]
        outliers = [s for s, z in zip(scores, z_scores) if abs(z) > 2.5]
        
        if outliers:
            # Check if this is historically unusual
            # (Simplified - would compare to historical mean)
            
            MalpracticePattern.objects.create(
                offering=offering,
                pattern_type="grade_outlier",
                z_score=float(max([abs(z) for z in z_scores])),
                detected_students=[str(s.student.id) for s in outliers],
            )
    
    # 2. MCQ similarity (would require answer pattern data)
    # This is placeholder - would need actual answer data
    
    return {"status": "success"}
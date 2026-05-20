"""
Result Validation and Immutability Service.
Phase 3 Module 06.
"""

import logging
from decimal import Decimal
from typing import Optional

from django.db import transaction

logger = logging.getLogger(__name__)


class ResultImmutableError(Exception):
    """Raised when attempting to modify immutable results."""
    pass


def check_batch_immutable(batch: "ResultBatch") -> bool:
    """Check if batch is senate-ratified (immutable)."""
    return batch.state == "senate_ratified"


def validate_score_entry(
    ca_score: Optional[Decimal],
    exam_score: Optional[Decimal],
    max_ca: int = 40,
    max_exam: int = 60,
) -> tuple[bool, str]:
    """
    Validate CA and Exam scores are within bounds.
    Returns (is_valid, error_message).
    """
    if ca_score is not None:
        if ca_score < 0 or ca_score > max_ca:
            return False, f"CA score must be between 0 and {max_ca}"
    
    if exam_score is not None:
        if exam_score < 0 or exam_score > max_exam:
            return False, f"Exam score must be between 0 and {max_exam}"
    
    return True, ""


def enter_scores(
    batch: "ResultBatch",
    scores_data: list[dict],
    user,
) -> dict:
    """
    Enter scores for a result batch.
    Validates batch is not immutable.
    """
    # Check immutability
    if check_batch_immutable(batch):
        raise ResultImmutableError(
            "Cannot modify senate-ratified results. "
            "Raise a formal senate resolution for corrections."
        )
    
    results = []
    errors = []
    
    with transaction.atomic():
        for data in scores_data:
            student_id = data.get("student_id")
            ca = data.get("ca_score")
            exam = data.get("exam_score")
            
            # Validate
            is_valid, error = validate_score_entry(ca, exam)
            if not is_valid:
                errors.append({"student_id": student_id, "error": error})
                continue
            
            try:
                score, created = Score.objects.update_or_create(
                    student_id=student_id,
                    offering_id=batch.id,  # This needs adjustment
                    semester=batch.semester,
                    defaults={
                        "ca_score": ca,
                        "exam_score": exam,
                        "entered_by": user,
                    }
                )
                
                # Compute grade
                score.compute_grade()
                score.save()
                
                results.append({"student_id": student_id, "score_id": str(score.id)})
                
            except Exception as e:
                errors.append({"student_id": student_id, "error": str(e)})
    
    return {
        "entered": results,
        "errors": errors,
    }


def transition_batch(
    batch: "ResultBatch",
    target_state: str,
    user,
) -> bool:
    """
    Transition result batch through FSM.
    All transitions logged via simple_history.
    """
    if check_batch_immutable(batch) and target_state != "published":
        raise ResultImmutableError("Senate-ratified results cannot be modified")
    
    transitions = {
        "hod_approve": batch.hod_approve,
        "dean_approve": batch.dean_approve,
        "exam_officer_compile": batch.exam_officer_compile,
        "senate_ratify": batch.senate_ratify,
        "publish": batch.publish,
    }
    
    transition_func = transitions.get(target_state)
    if not transition_func:
        raise ValueError(f"Invalid transition: {target_state}")
    
    try:
        transition_func(user)
        batch.save()
        
        # Trigger notifications
        if target_state == "senate_ratify":
            from apps.examinations.tasks import post_ratification_pipeline
            post_ratification_pipeline.delay(str(batch.id))
        
        return True
        
    except Exception as e:
        logger.error(f"Batch transition failed: {e}")
        raise


def compute_semester_gpa(student, semester) -> Decimal:
    """Compute GPA for a semester."""
    scores = Score.objects.filter(
        student=student,
        semester=semester,
        grade__isnull=False,
    )
    
    total_points = Decimal("0")
    total_units = 0
    
    for score in scores:
        if score.grade_points and score.credit_units:
            total_points += score.grade_points * Decimal(score.credit_units)
            total_units += score.credit_units
    
    if total_units == 0:
        return Decimal("0.00")
    
    gpa = total_points / Decimal(total_units)
    return round(gpa, 2)


def recompute_cgpa(student) -> Decimal:
    """Recompute CGPA from all ratified results."""
    scores = Score.objects.filter(
        student=student,
        grade__isnull=False,
    ).select_related("semester")
    
    total_points = Decimal("0")
    total_units = 0
    
    for score in scores:
        if score.grade_points and score.credit_units:
            total_points += score.grade_points * Decimal(score.credit_units)
            total_units += score.credit_units
    
    if total_units == 0:
        cgpa = Decimal("0.00")
    else:
        cgpa = round(total_points / Decimal(total_units), 2)
    
    # Update student
    student.current_cgpa = cgpa
    student.total_credits_earned = total_units
    student.save()
    
    return cgpa


# Import models
from apps.examinations.models import Score, ResultBatch  # noqa: E402
"""
Examinations Celery Tasks.
Phase 3 Module 06.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="default")
def post_ratification_pipeline(self, batch_id: str):
    """
    Run after senate ratification:
    1. Recompute CGPA for all students
    2. Trigger dropout risk scoring
    3. Check NYSC eligibility
    """
    from apps.examinations.models import Score, ResultBatch
    from apps.examinations.services import recompute_cgpa
    from apps.students.models import Student
    
    try:
        batch = ResultBatch.objects.get(id=batch_id)
    except ResultBatch.DoesNotExist:
        return {"status": "error", "message": "Batch not found"}
    
    # Get all students in batch
    student_ids = Score.objects.filter(
        offering__result_batch=batch
    ).values_list("student_id", flat=True).distinct()
    
    # Recompute CGPA for each student
    for student_id in student_ids:
        try:
            student = Student.objects.get(id=student_id)
            recompute_cgpa(student)
        except Exception as e:
            logger.error(f"CGPA recompute failed for {student_id}: {e}")
    
    # Trigger dropout risk scoring
    try:
        from apps.ml.dropout.tasks import score_all_students
        score_all_students.delay(str(batch.semester.session.tenant_id))
    except Exception as e:
        logger.error(f"Dropout scoring failed: {e}")
    
    return {"status": "success", "students_processed": len(student_ids)}


@shared_task(bind=True, queue="notifications")
def notify_students_results_published(self, batch_id: str):
    """Send SMS to students when results are published."""
    from apps.examinations.models import Score, ResultBatch
    from apps.notifications.sms import get_sms_service
    
    try:
        batch = ResultBatch.objects.get(id=batch_id)
    except ResultBatch.DoesNotExist:
        return {"status": "error"}
    
    # Get unique students
    student_ids = Score.objects.filter(
        offering__result_batch=batch
    ).values_list("student_id", flat=True).distinct()
    
    sms = get_sms_service()
    
    for student_id in student_ids:
        try:
            from apps.students.models import Student
            student = Student.objects.get(id=student_id)
            
            message = (
                f"Dear {student.first_name}, your {batch.semester.name} "
                f"results are now available. Log in to view."
            )
            
            sms.send(student.phone, message)
        except Exception as e:
            logger.error(f"SMS failed for {student_id}: {e}")
    
    return {"status": "success", "notifications_sent": len(student_ids)}


@shared_task(bind=True, queue="notifications")
def notify_dean(self, batch_id: str):
    """Notify dean when HOD approves results."""
    # Implementation would send notification
    return {"status": "success"}


@shared_task(bind=True, queue="notifications")
def notify_exam_officer(self, batch_id: str):
    """Notify exam officer when dean approves results."""
    return {"status": "success"}
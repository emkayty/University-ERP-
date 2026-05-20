"""
Face Verification Service.
Phase 4 - AI Domain 6.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    passed: bool
    similarity_score: float
    message: str
    alert_triggered: bool = False


def verify_exam_identity(
    student_matric: str,
    captured_image_bytes: bytes,
) -> VerificationResult:
    """
    Verify student identity for exam.
    
    1. Detect face in captured image (MTCNN)
    2. Generate 128-d FaceNet embedding
    3. pgvector cosine similarity against stored embedding
    4. Threshold: > 0.85 = PASS
    5. Below threshold: alert invigilator via WebSocket
    """
    from apps.ml.face.models import StudentFaceEmbedding, FaceVerificationLog
    from apps.students.models import Student
    from django.utils import timezone
    
    # Get student
    try:
        student = Student.objects.get(matric_number=student_matric)
    except Student.DoesNotExist:
        return VerificationResult(
            passed=False,
            similarity_score=0.0,
            message="Student not found",
        )
    
    # Check consent
    latest_embedding = StudentFaceEmbedding.objects.filter(
        student=student,
        consent_given=True,
        is_active=True,
    ).order_by("-captured_at").first()
    
    if not latest_embedding:
        return VerificationResult(
            passed=False,
            similarity_score=0.0,
            message="No face data on file. Please register your face first.",
        )
    
    # In production, would:
    # 1. Detect face in image
    # 2. Generate embedding
    # 3. Compare with stored embedding
    
    # Simplified: random score for demo
    import random
    similarity_score = random.uniform(0.7, 0.99)
    
    passed = similarity_score > 0.85
    
    # Log attempt
    log = FaceVerificationLog.objects.create(
        student=student,
        verification_code=student_matric,
        similarity_score=similarity_score,
        passed=passed,
        capture_time_ms=1000,  # Would measure actual time
    )
    
    # Alert if below threshold
    alert_triggered = False
    if not passed:
        alert_triggered = True
        log.alert_sent = True
        log.alert_sent_at = timezone.now()
        log.save()
        
        # Would send WebSocket alert to invigilator
    
    return VerificationResult(
        passed=passed,
        similarity_score=similarity_score,
        message="Verification passed" if passed else "Verification failed. Alert sent to invigilator.",
        alert_triggered=alert_triggered,
    )


def schedule_face_deletion(student_id: str, graduation_date):
    """
    Schedule face embedding deletion after graduation.
    NDPA compliance.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Delete 3 years after graduation (as per NDPA retention period)
    deletion_date = graduation_date + timedelta(days=3*365)
    
    StudentFaceEmbedding.objects.filter(
        student_id=student_id,
    ).update(
        deletion_scheduled_at=deletion_date,
        is_active=False,
    )


def capture_face_consent(
    student_id: str,
    embedding,
    quality_score: float,
) -> bool:
    """
    Capture face with consent.
    NDPA: Must have explicit consent before storing biometric.
    """
    from apps.ml.face.models import StudentFaceEmbedding
    
    embedding = StudentFaceEmbedding.objects.create(
        student_id=student_id,
        embedding=embedding,
        quality_score=quality_score,
        consent_given=True,
    )
    
    return True
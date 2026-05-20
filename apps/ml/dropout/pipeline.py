"""
Dropout Risk ML Pipeline.
Phase 3 - AI Domain 1.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Feature columns for dropout prediction
FEATURE_COLUMNS = [
    "attendance_pct_current_semester",
    "cgpa_slope_last_2_semesters",
    "days_since_last_fee_payment",
    "carry_over_course_count",
    "is_hostel_resident",
    "state_of_origin_first_gen_flag",
    "semesters_on_probation",
    "asuu_strike_affected_semesters",
]


def check_ml_data_readiness(tenant_id: str) -> bool:
    """
    Check if sufficient data exists for ML training.
    Minimum: 2 full academic sessions with ratified results.
    """
    from apps.institutional.models import AcademicSession
    from apps.examinations.models import ResultBatch
    
    sessions = AcademicSession.objects.filter(
        tenant_id=tenant_id,
        semesters__result_batches__state="senate_ratified",
    ).distinct().count()
    
    return sessions >= 2


def get_student_features(student_id: str) -> dict:
    """Extract features for a single student."""
    from apps.students.models import Student
    from apps.courses.models import CourseRegistration
    from apps.finance.models import Invoice
    from datetime import timedelta
    from django.utils import timezone
    
    features = {}
    
    try:
        student = Student.objects.get(id=student_id)
        
        # 1. Attendance - read from attendance module or raise if not available
        from apps.attendance.models import AttendanceRecord
        attendance = AttendanceRecord.objects.filter(
            student=student,
            semester=current_semester
        ).first()
        
        if attendance and attendance.attendance_rate is not None:
            features["attendance_pct_current_semester"] = attendance.attendance_rate
        else:
            # Data not available - cannot make prediction
            raise ValueError(
                f"Attendance data not available for student {student_id} "
                f"in semester {current_semester}"
            )
        
        # 2. CGPA slope - calculate from result history or raise
        from apps.examinations.models import Score
        scores = Score.objects.filter(
            student=student,
            semester__session__lte=current_semester
        ).order_by("-semester")[:4]
        
        if scores.count() >= 2:
            # Calculate CGPA trend
            gpas = [s.total_score / 100 * 5.0 for s in scores]
            slope = (gpas[0] - gpas[-1]) / max(1, len(gpas) - 1)
            features["cgpa_slope_last_2_semesters"] = slope
        else:
            raise ValueError(
                f"Insufficient score history for student {student_id} "
                f"(need at least 2 semesters)"
            )
        
        # 3. Days since last fee payment
        last_payment = Invoice.objects.filter(
            student=student,
            state="fully_paid",
        ).order_by("-created_at").first()
        
        if last_payment:
            days = (timezone.now() - last_payment.created_at).days
            features["days_since_last_fee_payment"] = days
        else:
            features["days_since_last_fee_payment"] = 999
        
        # 4. Carry over courses
        from apps.examinations.models import Score
        carry_overs = Score.objects.filter(
            student=student,
            grade__in=["E", "F"],
        ).count()
        features["carry_over_course_count"] = carry_overs
        
        # 5. Hostel resident
        from apps.hostel.models import HostelApplication
        features["is_hostel_resident"] = HostelApplication.objects.filter(
            student=student,
            state="checked_in",
        ).exists()
        
        # 6. First generation (placeholder - would need population data)
        features["state_of_origin_first_gen_flag"] = False
        
        # 7. Semesters on probation
        features["semesters_on_probation"] = 0  # Would calculate
        
        # 8. ASUU strike affected (placeholder)
        features["asuu_strike_affected_semesters"] = 0
        
    except Student.DoesNotExist:
        return {}
    
    return features


def score_dropout_risk(student_id: str) -> tuple[float, str, dict]:
    """
    Score dropout risk for a student.
    Returns (risk_score, risk_level, explanation).
    """
    from apps.ml.dropout.models import StudentRiskScore
    
    # Check data readiness
    try:
        student = Student.objects.get(id=student_id)
    except:
        return 0.0, "low", {}
    
    if not check_ml_data_readiness(str(student.user.tenant_id)):
        return 0.0, "low", {"status": "not_ready"}
    
    # Get features
    features = get_student_features(student_id)
    
    # Simplified scoring (would use trained model in production)
    risk_score = 0.0
    
    # CGPA slope
    cgpa_slope = features.get("cgpa_slope_last_2_semesters", 0)
    if cgpa_slope < -0.5:
        risk_score += 0.3
    
    # Attendance
    attendance = features.get("attendance_pct_current_semester", 100)
    if attendance < 75:
        risk_score += 0.25
    
    # Fee payment
    days_since = features.get("days_since_last_fee_payment", 0)
    if days_since > 90:
        risk_score += 0.2
    
    # Carry overs
    carry_overs = features.get("carry_over_course_count", 0)
    if carry_overs >= 3:
        risk_score += 0.15
    
    # Cap at 1.0
    risk_score = min(risk_score, 1.0)
    
    # Determine level
    if risk_score >= 0.7:
        level = "critical"
    elif risk_score >= 0.5:
        level = "high"
    elif risk_score >= 0.3:
        level = "medium"
    else:
        level = "low"
    
    # Build explanation
    explanation = {
        "top_factors": [],
    }
    
    if cgpa_slope < -0.5:
        explanation["top_factors"].append({"factor": "declining_cgpa", "contribution": 0.3})
    if attendance < 75:
        explanation["top_factors"].append({"factor": "low_attendance", "contribution": 0.25})
    if days_since > 90:
        explanation["top_factors"].append({"factor": "fee_arrears", "contribution": 0.2})
    
    return risk_score, level, explanation


# Import at bottom to avoid circular imports
from apps.students.models import Student  # noqa: E402
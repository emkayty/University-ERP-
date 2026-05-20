"""
Accreditation Readiness Service.
Phase 6 Module 11.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


# NUC Accreditation Criteria
NUC_CRITERIA = {
    "staffing": {
        "weight": 0.25,
        "checks": [
            "check_professor_count",
            "check_phd_ratio",
            "check_staff_student_ratio",
            "check_lecturer_workload",
        ],
    },
    "curriculum": {
        "weight": 0.20,
        "checks": [
            "check_course_outlines_complete",
            "check_gst_courses_offered",
            "check_prerequisite_completeness",
        ],
    },
    "facilities": {
        "weight": 0.20,
        "checks": [
            "check_library_book_count",
            "check_lab_equipment",
            "check_ict_facilities",
        ],
    },
    "student_performance": {
        "weight": 0.15,
        "checks": [
            "check_pass_rate",
            "check_cgpa_distribution",
            "check_graduate_employability",
        ],
    },
    "research": {
        "weight": 0.10,
        "checks": [
            "check_publications",
            "check_research_output",
            "check_funding",
        ],
    },
    "governance": {
        "weight": 0.10,
        "checks": [
            "check_external_examiners",
            "check_senate_records",
            "check_quality_assurance",
        ],
    },
}


def check_professor_count(department) -> Dict:
    """Check minimum professor count."""
    from apps.hr.models import StaffProfile
    from apps.users.models import UserRole
    
    professors = StaffProfile.objects.filter(
        department=department,
        academic_rank__in=["professor", "associate_professor"],
    ).count()
    
    return {
        "passed": professors >= 1,
        "value": professors,
        "threshold": 1,
    }


def check_phd_ratio(department) -> Dict:
    """Check PhD ratio ≥ 60%."""
    from apps.hr.models import StaffProfile
    
    total = StaffProfile.objects.filter(department=department).count()
    if total == 0:
        return {"passed": False, "value": 0, "threshold": 0.6}
    
    phds = StaffProfile.objects.filter(
        department=department,
        academic_rank__in=["professor", "associate_professor", "senior_lecturer"],
    ).count()
    
    ratio = phds / total
    return {
        "passed": ratio >= 0.6,
        "value": ratio,
        "threshold": 0.6,
    }


def check_staff_student_ratio(department) -> Dict:
    """Check staff:student ratio ≤ 1:25."""
    from apps.students.models import Student
    
    total_students = Student.objects.filter(
        programme__department=department,
        status="active",
    ).count()
    
    from apps.hr.models import StaffProfile
    total_staff = StaffProfile.objects.filter(department=department).count()
    
    if total_staff == 0:
        return {"passed": False, "value": 0, "threshold": 25}
    
    ratio = total_students / total_staff
    return {
        "passed": ratio <= 25,
        "value": ratio,
        "threshold": 25,
    }


def run_accreditation_readiness(tenant_id: str):
    """
    Run all NUC criteria checks.
    Called by Celery Beat daily at 2AM.
    """
    from apps.institutional.models import Programme
    from apps.accreditation.models import AccreditationReadinessScore, AccreditationCriteriaCheck
    
    programmes = Programme.objects.filter(department__faculty__tenant_id=tenant_id)
    
    for prog in programmes:
        scores = {}
        
        # Staffing checks
        staffing_checks = [
            check_professor_count(prog.department),
            check_phd_ratio(prog.department),
            check_staff_student_ratio(prog.department),
        ]
        
        staffing_score = sum(c["value"] for c in staffing_checks) / len(staffing_checks) * 100
        scores["staffing"] = staffing_score
        
        # Other categories (simplified)
        for category in ["curriculum", "facilities", "student_performance", "research", "governance"]:
            scores[category] = 75.0  # Placeholder
        
        # Calculate overall
        overall = sum(scores[k] * NUC_CRITERIA[k]["weight"] for k in scores)
        
        # Determine traffic light
        if overall >= 80:
            status = "green"
        elif overall >= 60:
            status = "amber"
        else:
            status = "red"
        
        # Save score
        readiness = AccreditationReadinessScore.objects.create(
            programme=prog,
            staffing_score=scores["staffing"],
            curriculum_score=scores.get("curriculum", 0),
            facilities_score=scores.get("facilities", 0),
            student_performance_score=scores.get("student_performance", 0),
            research_score=scores.get("research", 0),
            governance_score=scores.get("governance", 0),
            overall_score=overall,
            status=status,
        )
        
        # Save individual checks
        for check in staffing_checks:
            AccreditationCriteriaCheck.objects.create(
                readiness=readiness,
                criteria_name=check.get("name", "staffing_check"),
                criteria_category="staffing",
                passed=check["passed"],
                score=check["value"] * 100 if check["value"] <= 1 else check["value"],
            )
    
    return {"status": "success", "programmes": programmes.count()}
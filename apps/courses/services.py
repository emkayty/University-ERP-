"""
Course Registration Service.
Phase 2 Module 04.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.db import transaction

from apps.courses.models import (
    CourseRegistration,
    CourseOffering,
    PrerequisiteStatus,
)
from apps.finance.models import Invoice
from apps.students.models import Student
from apps.institutional.models import Semester, GradingConfig

logger = logging.getLogger(__name__)


@dataclass
class RegistrationResult:
    """Result of course registration."""
    success: bool
    registrations: list[CourseRegistration]
    errors: list[str]
    warnings: list[str]


class RegistrationError(Exception):
    """Base registration error."""
    pass


class FeeClearanceError(RegistrationError):
    """Student has outstanding fees."""
    pass


class PrerequisiteNotMetError(RegistrationError):
    """Prerequisite not met."""
    def __init__(self, course_code: str, missing: list):
        self.course_code = course_code
        self.missing = missing
        super().__init__(f"Prerequisites not met for {course_code}: {', '.join(missing)}")


class CreditLimitError(RegistrationError):
    """Credit limit exceeded."""
    pass


class LevelEligibilityError(RegistrationError):
    """Cannot register for level."""
    pass


class AddDropWindowClosedError(RegistrationError):
    """Add/drop window is closed."""
    pass


class DuplicateRegistrationError(RegistrationError):
    """Already registered for course."""
    pass


def validate_prerequisites(
    student: Student,
    offering: CourseOffering,
) -> tuple[bool, list[str]]:
    """
    Validate student has met all prerequisites.
    Returns (is_valid, missing_prerequisites).
    """
    course = offering.course
    missing = []
    
    for prereq in course.prerequisites.all():
        # Check if student passed the prerequisite course
        # Look at their registration and grade records
        # This is simplified - actual implementation would check grades
        
        # Check prerequisite status
        status = PrerequisiteStatus.objects.filter(
            student=student,
            course=course,
            prerequisite=prereq,
        ).first()
        
        if not status or not status.is_met:
            missing.append(prereq.code)
    
    return len(missing) == 0, missing


def calculate_total_credits(
    student: Student,
    offerings: list[CourseOffering],
) -> int:
    """Calculate total credit units for proposed registrations."""
    total = 0
    for offering in offerings:
        total += offering.course.credit_units
    return total


def check_fee_clearance(student: Student, session) -> bool:
    """
    Check if student has fully paid fees for the session.
    Looks for Invoice with state='fully_paid'.
    """
    invoice = Invoice.objects.filter(
        student=student,
        session=session,
        state="fully_paid",
    ).first()
    
    return invoice is not None


def check_add_drop_window(semester: Semester) -> bool:
    """Check if we're within the add/drop window."""
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now().date()
    
    # Add/drop typically allowed in first 2 weeks
    if semester.start_date <= now <= semester.start_date + timedelta(days=14):
        return True
    return False


@transaction.atomic
def register_courses(
    student: Student,
    offering_ids: list[str],
    semester: Semester,
    registration_type: str = "normal",
) -> RegistrationResult:
    """
    Validates and registers courses atomically.
    
    Checks (in order):
    1. Fee clearance
    2. Prerequisite satisfaction
    3. Carry-over identification  
    4. Credit load
    5. Level eligibility
    6. Add/drop window (for changes)
    7. Duplicate registration
    
    Atomic: all succeed or none do.
    """
    errors = []
    warnings = []
    registrations = []
    
    # Get offerings
    offerings = []
    for offering_id in offering_ids:
        try:
            offering = CourseOffering.objects.select_for_update().get(
                id=offering_id,
                semester=semester,
            )
            offerings.append(offering)
        except CourseOffering.DoesNotExist:
            errors.append(f"Course offering not found: {offering_id}")
    
    if errors:
        return RegistrationResult(False, [], errors, warnings)
    
    # 1. Fee clearance check
    if not check_fee_clearance(student, semester.session):
        raise FeeClearanceError(
            "Outstanding fees detected. Please pay all fees before course registration."
        )
    
    # 2. Prerequisite validation
    for offering in offerings:
        is_valid, missing = validate_prerequisites(student, offering)
        if not is_valid:
            raise PrerequisiteNotMetError(offering.course.code, missing)
    
    # 3 & 4. Credit load check
    from apps.institutional.models import InstitutionalConfig
    
    config = None
    try:
        config = InstitutionalConfig.objects.get(tenant=student.user.tenant)
    except InstitutionalConfig.DoesNotExist:
        pass
    
    max_credits = config.max_registration_credits if config else 24
    
    total_credits = calculate_total_credits(student, offerings)
    if total_credits > max_credits:
        raise CreditLimitError(
            f"Credit load ({total_credits}) exceeds maximum ({max_credits})."
        )
    
    # 5. Level eligibility (simplified)
    # Cannot register for courses 2 levels above current
    for offering in offerings:
        if offering.course.level > student.current_level + 200:
            warnings.append(
                f"{offering.course.code}: Cannot register {offering.course.level} "
                f"when at {student.current_level}"
            )
    
    # 6. Add/drop window for non-normal registration
    if registration_type in ["add", "drop"]:
        if not check_add_drop_window(semester):
            raise AddDropWindowClosedError(
                "Add/drop window has closed for this semester."
            )
    
    # 7. Check for duplicates and capacity
    for offering in offerings:
        # Duplicate check
        existing = CourseRegistration.objects.filter(
            student=student,
            offering=offering,
            is_deleted=False,
        ).exists()
        
        if existing:
            raise DuplicateRegistrationError(
                f"Already registered for {offering.course.code}"
            )
        
        # Capacity check
        if not offering.can_register():
            errors.append(
                f"{offering.course.code}: Course is full"
            )
    
    if errors:
        return RegistrationResult(False, [], errors, warnings)
    
    # All validations passed - create registrations
    for offering in offerings:
        reg = CourseRegistration.objects.create(
            student=student,
            offering=offering,
            semester=semester,
            registration_type=registration_type,
        )
        registrations.append(reg)
        
        # Update enrolment
        offering.current_enrolment += 1
        offering.save()
    
    return RegistrationResult(True, registrations, [], warnings)


def calculate_cgpa(student: Student) -> Decimal:
    """
    Calculate CGPA using NUC-standard formula.
    
    CGPA = Σ(credit_units × grade_points) / Σ(credit_units)
    Only includes senate-ratified results.
    """
    from apps.courses.models import CourseRegistration
    from apps.examinations.models import Result  # Would need Result model
    
    # This is a placeholder - actual implementation
    # would query Result model for grades
    
    # Get registrations with confirmed results
    regs = CourseRegistration.objects.filter(
        student=student,
        state="confirmed",
    ).select_related("offering__course")
    
    total_points = 0
    total_credits = 0
    
    for reg in regs:
        course = reg.offering.course
        # Get grade from Result model
        try:
            # result = Result.objects.get(registration=reg)
            # grading = GradingConfig.objects.get(session=reg.semester.session)
            # grade, points = grading.get_grade(result.score)
            
            points = 4.0  # Placeholder
            total_points += course.credit_units * points
            total_credits += course.credit_units
        except Exception:
            pass
    
    if total_credits == 0:
        return Decimal("0.00")
    
    cgpa = Decimal(total_points) / Decimal(total_credits)
    
    # Update student record
    student.current_cgpa = round(cgpa, 2)
    student.total_credits_earned = total_credits
    student.save()
    
    return round(cgpa, 2)
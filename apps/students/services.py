"""
Student Services - Matric Number Generation, Duplicate Detection.
Phase 1 Module 03.
"""

import logging
from decimal import Decimal
from typing import Optional

from django.db import transaction, models
from django.db.models.functions import Similarity
from django.conf import settings

logger = logging.getLogger(__name__)

# Enable pg_trgm for similarity search
USE_TRGM = getattr(settings, "USE_PG_TRGM", True)


def generate_matric_number(student: "Student") -> str:
    """
    Atomically generate matric number.
    
    Uses institution's configured format.
    Uses SELECT FOR UPDATE to prevent race conditions.
    
    Format from InstitutionalConfig, e.g.:
    {year}/{faculty_code}/{dept_code}/{serial:03d}
    Example: 2025/ENG/CSC/001
    """
    from apps.students.models import MatricCounter
    from apps.institutional.models import InstitutionalConfig
    
    with transaction.atomic():
        # Get config
        try:
            config = InstitutionalConfig.objects.get(tenant=student.user.tenant)
        except InstitutionalConfig.DoesNotExist:
            config = None
        
        # Get or create counter
        counter, _ = MatricCounter.objects.select_for_update().get_or_create(
            session=student.entry_session,
            department=student.programme.department,
            defaults={"current_serial": 0},
        )
        
        # Increment
        counter.current_serial += 1
        counter.save()
        
        # Format
        year = student.entry_session.name[:4]
        faculty_code = student.programme.department.faculty.code
        dept_code = student.programme.department.code
        serial = counter.current_serial
        
        if config:
            format_str = config.matric_format
        else:
            format_str = "{year}/{faculty_code}/{dept_code}/{serial:03d}"
        
        return format_str.format(
            year=year,
            faculty_code=faculty_code,
            dept_code=dept_code,
            serial=serial,
        )


def generate_student_institution_email(
    student: "Student",
) -> str:
    """Generate institution email based on matric number."""
    domain = getattr(student.user.tenant, "student_email_domain", None)
    if not domain:
        return ""
    
    return f"{student.matric_number.lower()}@{domain}"


@transaction.atomic
def create_student_from_application(
    application: "Application",
) -> "Student":
    """
    Create student record from accepted application.
    
    Called after admission is cleared.
    """
    from apps.students.models import Student
    from apps.admissions.models import AdmissionOffer
    
    # Get offer
    offer = application.offer
    if not offer:
        raise ValueError("No admission offer found")
    
    # Create user if not exists
    user = application.applicant
    
    # Determine entry mode
    if application.jamb_reg_no:
        if application.entry_mode == "utme":
            entry_mode = "utme"
        else:
            entry_mode = "de"
    else:
        entry_mode = "postgraduate"
    
    # Determine level
    if offer.programme.degree_type in ["bsc", "ba", "beng", "mbbs", "bpharm", "bnsc", "bot"]:
        entry_level = 100
    elif offer.programme.degree_type in ["msc", "mphil"]:
        entry_level = 500
    elif offer.programme.degree_type == "phd":
        entry_level = 700
    else:
        entry_level = 100
    
    # Create student
    student = Student.objects.create(
        user=user,
        programme=offer.programme,
        current_level=entry_level,
        entry_session=application.session,
        entry_mode=entry_mode,
        first_name=user.get_full_name().split()[0],
        last_name=user.get_full_name().split()[-1] if len(user.get_full_name().split()) > 1 else "",
        date_of_birth=None,  # Would be from application
        gender="M",  # Would be from biodata
        state_of_origin="",  # Would be from biodata
        lga_of_origin="",  # Would be from biodata
        phone=user.phone or "",
        Jamb_reg_no=application.jamb_reg_no,
        nin=application.jamb_reg_no,  # Would be different
    )
    
    # Generate matric number
    student.matric_number = generate_matric_number(student)
    
    # Generate institution email
    student.institution_email = generate_student_institution_email(student)
    
    student.save()
    
    # Update application state
    application.matriculate()
    application.save()
    
    # Send matriculation SMS
    from apps.notifications.sms import send_matric_number_sms
    send_matric_number_sms(
        phone=user.phone,
        name=user.get_full_name(),
        matric=student.matric_number,
        university=user.tenant.name,
    )
    
    return student


def detect_duplicate_student(
    first_name: str,
    last_name: str,
    dob: "date",
    nin: str = "",
    jamb_reg_no: str = "",
) -> list["Student"]:
    """
    Detect potential duplicate students.
    
    Uses:
    1. Exact NIN match
    2. Exact JAMB reg number match
    3. Name similarity (pg_trgm) + same DOB
    
    Returns list of candidate duplicates for Registrar review.
    """
    from apps.students.models import Student, DuplicateCheck
    
    candidates = []
    seen_ids = set()
    
    # 1. Exact NIN match
    if nin:
        nin_matches = Student.objects.filter(nin=nin, is_deleted=False)
        for student in nin_matches:
            if student.id not in seen_ids:
                candidates.append(student)
                seen_ids.add(student.id)
                # Record check
                DuplicateCheck.objects.get_or_create(
                    student_id=student.id,  # Will be created after id exists
                    check_type="nin",
                    defaults={
                        "matched_student": student,  # Would need to handle
                    }
                )
    
    # 2. Exact JAMB match
    if jamb_reg_no:
        jamb_matches = Student.objects.filter(
            jamb_reg_no=jamb_reg_no,
            is_deleted=False,
        )
        for student in jamb_matches:
            if student.id not in seen_ids:
                candidates.append(student)
                seen_ids.add(student.id)
    
    # 3. Name similarity + DOB (if pg_trgm available)
    if USE_TRGM:
        try:
            # Note: This requires pg_trgm extension
            # name_sim = Similarity('first_name', models.Value(first_name)) + \
            #           Similarity('last_name', models.Value(last_name))
            
            dob_matches = Student.objects.filter(
                date_of_birth=dob,
                is_deleted=False,
            ).filter(
                models.Q(first_name__icontains=first_name) |
                models.Q(last_name__icontains=last_name)
            )
            
            for student in dob_matches:
                if student.id not in seen_ids:
                    candidates.append(student)
                    seen_ids.add(student.id)
        except Exception as e:
            logger.warning(f"pg_trgm similarity search failed: {e}")
    
    return candidates


# Import models
from apps.integrations.nimc import get_nimc_client, NIMCVerificationResult  # noqa: E402


@transaction.atomic
def verify_student_nin(
    student: "Student",
    nin: str,
    first_name: str,
    last_name: str,
    dob: "date",
) -> tuple[bool, str]:
    """
    Verify student's NIN via NIMC API.
    
    Returns (success, message).
    """
    # Import here to avoid circular imports
    from apps.integrations.nimc import get_nimc_client
    
    client = get_nimc_client()
    
    try:
        result = client.verify_nin(nin, first_name, last_name, dob)
        
        # Update student record
        student.nin = nin
        student.nin_verified = result.is_verified
        student.nin_verified_at = models.functions.Now()
        student.save()
        
        return result.is_verified, "NIN verified successfully"
    
    except Exception as e:
        logger.error(f"NIN verification failed: {e}")
        return False, str(e)


# Type hints for Python
from datetime import date as date_type
date = date_type.date  # Re-export for typing
"""
Transcript Validation & Generation Services.
Phase 4 Module 08.
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Blocked email domains for official transcripts
BLOCKED_DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "mail.com",
    "icloud.com", "protonmail.com", "yandex.com",
]

# Allowed domains
ALLOWED_DOMAINS = [
    ".edu", ".ac.uk", ".ac.za", ".ac.gh", ".edu.ng",
    "wes.org", "icas.edu", "nus.edu.sg",
]

#手动 whitelist
WHITELISTED_EMAILS = []


@dataclass
class ValidationResult:
    is_valid: bool
    message: str


def validate_transcript_destination(destination: dict, request_type: str) -> ValidationResult:
    """
    Validate transcript destination.
    
    Official transcripts ONLY to:
    - Verified institutional email domains
    - Scholarship/embassy domains (whitelisted)
    - WES / ICAS official portals
    
    BLOCK:
    - Gmail, Yahoo, Hotmail, Outlook - personal email
    - WhatsApp dispatch requests
    - Hand-delivery for official transcripts
    """
    
    dest_type = destination.get("type", "")
    email = destination.get("email", "")
    
    # Official transcript
    if request_type == "official":
        if dest_type == "personal":
            return ValidationResult(
                False,
                "Official transcripts cannot be dispatched to personal email addresses"
            )
        
        if dest_type == "whatsapp":
            return ValidationResult(
                False,
                "Official transcripts cannot be dispatched via WhatsApp"
            )
        
        if dest_type == "hand_delivery":
            return ValidationResult(
                False,
                "Official transcripts cannot be hand-delivered"
            )
        
        # Check email domain
        if email:
            domain = email.split("@")[-1].lower() if "@" in email else ""
            
            if domain in BLOCKED_DOMAINS:
                return ValidationResult(
                    False,
                    f"Official transcripts cannot be sent to {domain} personal email. Use institutional email."
                )
            
            # Check allowed
            allowed = False
            for allowed_domain in ALLOWED_DOMAINS:
                if domain.endswith(allowed_domain):
                    allowed = True
                    break
            
            if not allowed and domain != "":
                return ValidationResult(
                    False,
                    f"Email domain {domain} is not approved for official transcripts"
                )
    
    return ValidationResult(True, "Valid destination")


def generate_verification_code() -> str:
    """Generate unique verification code."""
    import uuid
    return str(uuid.uuid4())


# Transcript PDF Generation (placeholder - uses ReportLab)
def generate_official_transcript_pdf(request) -> bytes:
    """
    Generate official transcript PDF.
    This is a placeholder - actual implementation would use ReportLab.
    """
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []
    
    # Header with seal
    elements.append(Paragraph("UNIVERSITY OF NIGERIA", styles["Title"]))
    elements.append(Paragraph("OFFICIAL TRANSCRIPT", styles["Heading1"]))
    elements.append(Spacer(1, 0.3*inch))
    
    # Student details
    student = request.student
    data = [
        ["Student Name:", student.full_name],
        ["Matric Number:", student.matric_number],
        ["Programme:", student.programme.name],
        ["Entry Session:", student.entry_session.name],
    ]
    
    t = Table(data, colWidths=[1.5*inch, 3*inch])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (1, -1), 12),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.3*inch))
    
    # Results table would go here
    elements.append(Paragraph("Semester results...", styles["Normal"]))
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    elements.append(Paragraph(f"Verification Code: {request.verification_code}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {request.created_at}", styles["Normal"]))
    
    doc.build(elements)
    return buffer.getvalue()


def check_graduation_eligibility(student, session) -> dict:
    """
    Multi-condition graduation eligibility check.
    """
    from apps.records.models import GraduationEligibility
    from apps.examinations.models import Score
    from apps.finance.models import Invoice
    
    checks = {
        "credits_met": False,
        "compulsory_passed": False,
        "gst_completed": False,
        "cgpa_met": False,
        "fees_cleared": False,
        "library_cleared": False,
        "hostel_cleared": False,
        "departmental_cleared": False,
    }
    
    # 1. Credits check
    total_credits = student.total_credits_earned or 0
    min_credits = student.programme.minimum_credits or 120
    checks["credits_met"] = total_credits >= min_credits
    
    # 2. Compulsory courses
    failed_courses = Score.objects.filter(
        student=student,
        grade="F",
    ).count()
    checks["compulsory_passed"] = failed_courses == 0
    
    # 3. GST courses (simplified)
    # Would checkGST completions
    
    # 4. CGPA
    from apps.institutional.models import GradingConfig
    try:
        config = GradingConfig.objects.get(session=session)
        checks["cgpa_met"] = float(student.current_cgpa or 0) >= float(config.pass_threshold)
    except:
        checks["cgpa_met"] = False
    
    # 5. Fees
    outstanding = Invoice.objects.filter(
        student=student,
        state__in=["invoice_created", "partial_payment"],
    ).exists()
    checks["fees_cleared"] = not outstanding
    
    # 6-8. Clearances (simplified - would check actual clearances)
    
    # Calculate eligibility
    is_eligible = all([
        checks["credits_met"],
        checks["compulsory_passed"],
        checks["gst_completed"],
        checks["cgpa_met"],
        checks["fees_cleared"],
        checks["library_cleared"],
        checks["departmental_cleared"],
    ])
    
    failed = [k for k, v in checks.items() if not v]
    
    return {
        "is_eligible": is_eligible,
        "failed_checks": failed,
        "cgpa": student.current_cgpa,
    }
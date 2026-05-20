"""
Transcript & Records Models.
Phase 4 Module 08.
"""

import uuid
from django.db import models
from django.db.models import UniqueConstraint
from django_fsm import FSMField, transition
from apps.core.models import BaseModel


class TranscriptRequest(BaseModel):
    """Transcript request model."""
    
    REQUEST_TYPES = [
        ("official", "Official — Senate Authenticated"),
        ("student_copy", "Student Copy — Watermarked"),
        ("statement_of_results", "Statement of Results"),
        ("attestation", "Attestation Letter"),
        ("english_medium", "English as Medium of Instruction"),
    ]
    
    DELIVERY_METHODS = [
        ("digital", "Digital — Encrypted Email"),
        ("courier", "Courier Dispatch"),
        ("pickup", "Registry Pickup"),
    ]
    
    PROCESSING_TIERS = [
        ("standard", "Standard — 5 to 7 Days"),
        ("express", "Express — 48 Hours"),
    ]
    
    STATE_CHOICES = [
        ("requested", "Requested"),
        ("payment_verified", "Payment Verified"),
        ("processing", "Processing"),
        ("generated", "Generated"),
        ("dispatched", "Dispatched"),
        ("delivered", "Delivered"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="transcript_requests",
    )
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS)
    destination = models.JSONField()  # {"type": "university", "name": "...", "email": "..."}
    purpose = models.CharField(max_length=200)
    processing_tier = models.CharField(max_length=20, choices=PROCESSING_TIERS, default="standard")
    state = FSMField(default="requested", choices=STATE_CHOICES)
    
    # Generated file
    generated_file = models.FileField(null=True, blank=True, upload_to="transcripts/")
    verification_code = models.UUIDField(default=uuid.uuid4, unique=True)
    verification_url = models.URLField(blank=True)
    
    # Dispatch
    dispatch_waybill = models.CharField(max_length=100, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    
    # Fees
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    fee_paid = models.BooleanField(default=False)

    class Meta:
        db_table = "records_transcript_request"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "state"]),
            models.Index(fields=["verification_code"]),
        ]

    def __str__(self) -> str:
        return f"Transcript {self.id} - {self.student.matric_number} - {self.request_type}"

    @transition(field=state, source="requested", target="payment_verified")
    def verify_payment(self):
        self.fee_paid = True

    @transition(field=state, source="payment_verified", target="processing")
    def start_processing(self):
        pass

    @transition(field=state, source="processing", target="generated")
    def mark_generated(self):
        pass

    @transition(field=state, source="generated", target="dispatched")
    def dispatch(self):
        from django.utils import timezone
        self.dispatched_at = timezone.now()

    @transition(field=state, source="dispatched", target="delivered")
    def deliver(self):
        pass


class GraduationEligibility(BaseModel):
    """Graduation eligibility check."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="graduation_eligibility",
    )
    graduation_session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="graduations",
    )
    
    # Checks
    credits_met = models.BooleanField(default=False)
    compulsory_passed = models.BooleanField(default=False)
    gst_completed = models.BooleanField(default=False)
    cgpa_met = models.BooleanField(default=False)
    fees_cleared = models.BooleanField(default=False)
    library_cleared = models.BooleanField(default=False)
    hostel_cleared = models.BooleanField(default=False)
    departmental_cleared = models.BooleanField(default=False)
    
    is_eligible = models.BooleanField(default=False)
    failed_checks = models.JSONField(default=list)
    
    final_cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    degree_class = models.CharField(max_length=30, blank=True)
    
    applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "records_graduation_eligibility"
        constraints = [
            UniqueConstraint(
                fields=["student", "graduation_session"],
                name="unique_eligibility_per_session"
            )
        ]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.graduation_session.name}: {'ELIGIBLE' if self.is_eligible else 'NOT ELIGIBLE'}"
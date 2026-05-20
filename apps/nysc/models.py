"""
NYSC Mobilisation Models.
Phase 4 Module 10.
"""

from django.db import models

from apps.core.models import BaseModel


class NYSCEligibleGraduate(BaseModel):
    """NYSC eligibility and mobilisation tracking."""
    
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="nysc_records",
    )
    graduation_session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="nysc_graduates",
    )
    final_cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    degree_class = models.CharField(max_length=30)
    degree_certificate_serial = models.CharField(max_length=50, unique=True)
    
    # Eligibility checks
    age_eligible = models.BooleanField(default=True)
    is_citizen = models.BooleanField(default=True)
    nysc_batch = models.CharField(max_length=5, blank=True)
    nysc_batch_year = models.PositiveSmallIntegerField(null=True)
    
    # Name harmonisation
    matric_name = models.CharField(max_length=200)
    jamb_name = models.CharField(max_length=200)
    olevel_name = models.CharField(max_length=200, blank=True)
    name_discrepancy_flag = models.BooleanField(default=False)
    name_discrepancy_notes = models.TextField(blank=True)
    
    # NYSC portal status
    nysc_upload_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending Upload"),
            ("uploaded", "Uploaded"),
            ("accepted", "Accepted by NYSC"),
            ("rejected", "Rejected — Needs Correction"),
        ],
        default="pending",
    )
    nysc_uploaded_at = models.DateTimeField(null=True)
    nysc_uploaded_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    
    call_up_letter_received = models.BooleanField(default=False)
    call_up_date = models.DateField(null=True)
    ppa_posted = models.CharField(max_length=200, blank=True)
    ppa_posted_date = models.DateField(null=True)
    discharge_certificate_received = models.BooleanField(default=False)
    discharge_date = models.DateField(null=True)

    class Meta:
        db_table = "nysc_eligible_graduate"
        ordering = ["-graduation_session", "-final_cgpa"]
        indexes = [
            models.Index(fields=["graduation_session", "nysc_upload_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.graduation_session.name}"


class NYSCBatchExport(BaseModel):
    """NYSC batch export tracking."""
    session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="nysc_exports",
    )
    batch = models.CharField(max_length=5)  # A, B, C
    export_file = models.FileField(upload_to="nysc/exports/", null=True, blank=True)
    exported_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
    )
    exported_at = models.DateTimeField(auto_now_add=True)
    record_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "nysc_batch_export"

    def __str__(self) -> str:
        return f"NYSC {self.session.name} Batch {self.batch}"
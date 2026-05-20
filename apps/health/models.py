"""
Health Centre Models.
Phase 5 Module 13.
"""

from django.db import models
from datetime import timedelta
from django.utils import timezone

from apps.core.models import BaseModel


class StudentHealthRecord(BaseModel):
    """Student health record."""
    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="health_record",
    )
    blood_group = models.CharField(max_length=5)
    genotype = models.CharField(max_length=5)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    # NDPA: retention 10 years
    retention_until = models.DateField(null=True)

    class Meta:
        db_table = "health_record"

    def __str__(self) -> str:
        return f"Health: {self.student.matric_number}"

    def save(self, *args, **kwargs):
        if not self.retention_until:
            self.retention_until = timezone.now().date() + timedelta(days=365*10)
        super().save(*args, **kwargs)


class MedicalAppointment(BaseModel):
    """Medical appointment record."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="medical_appointments",
    )
    appointment_date = models.DateTimeField()
    doctor = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="medical_appointments",
    )
    symptoms = models.TextField()
    diagnosis = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    exam_excuse_issued = models.BooleanField(default=False)
    exam_excuse_valid_until = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "medical_appointment"
        ordering = ["-appointment_date"]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.appointment_date}"


class HealthCentreClearance(BaseModel):
    """Health clearance for graduation."""
    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="health_clearance",
    )
    is_cleared = models.BooleanField(default=True)  # Assume cleared unless medical condition
    medical_conditions_noted = models.TextField(blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)
    cleared_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "health_clearance"

    def __str__(self) -> str:
        return f"Health: {self.student.matric_number}"
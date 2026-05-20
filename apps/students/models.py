"""
Student Models - Biodata, Identity, Matriculation.
Phase 1 Module 03.
"""

import uuid
from datetime import date

from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone

from apps.core.models import BaseModel


class Student(BaseModel):
    """Student model with full biodata."""
    
    # Choices
    STATUS_CHOICES = [
        ("active", "Active"),
        ("deferred", "Deferred"),
        ("suspended", "Suspended"),
        ("rusticated", "Rusticated"),
        ("graduated", "Graduated"),
        ("withdrawn", "Withdrawn"),
        ("transferred", "Transferred"),
    ]
    
    ENTRY_MODE_CHOICES = [
        ("utme", "UTME"),
        ("de", "Direct Entry"),
        ("transfer", "Transfer"),
        ("postgraduate", "Postgraduate"),
    ]
    
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]
    
    # User link
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    
    # Academic
    matric_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
    )
    programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="students",
    )
    current_level = models.PositiveSmallIntegerField(
        choices=[
            (100, "100 Level"),
            (200, "200 Level"),
            (300, "300 Level"),
            (400, "400 Level"),
            (500, "500 Level"),
            (600, "600 Level"),
            (700, "700 Level"),
        ]
    )
    entry_session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="+",
    )
    entry_mode = models.CharField(
        max_length=20,
        choices=ENTRY_MODE_CHOICES,
    )
    
    # ML Enhancement - First generation student flag (Domain 1)
    # Identifies students whose parents/guardians did not attend university
    is_first_generation = models.BooleanField(
        default=False,
        help_text="First-generation university student"
    )
    parent_highest_education = models.CharField(
        max_length=30,
        choices=[
            ("none", "No Formal Education"),
            ("primary", "Primary"),
            ("secondary", "Secondary"),
            ("tertiary", "Tertiary"),
            ("unknown", "Unknown"),
        ],
        default="unknown",
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    
    # Identity Documents
    nin = models.CharField(max_length=11, blank=True, db_index=True)
    nin_verified = models.BooleanField(default=False)
    nin_verified_at = models.DateTimeField(null=True, blank=True)
    jamb_reg_no = models.CharField(max_length=20, blank=True)
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    state_of_origin = models.CharField(max_length=50)  # Nigerian state
    lga_of_origin = models.CharField(max_length=100)
    religion = models.CharField(max_length=50, blank=True)
    nationality = models.CharField(max_length=50, default="Nigerian")
    
    # Contact Information
    phone = models.CharField(max_length=20)
    phone_verified = models.BooleanField(default=False)
    personal_email = models.EmailField(blank=True)
    institution_email = models.EmailField(blank=True)
    permanent_address = models.TextField()
    contact_address = models.TextField(blank=True)
    
    # Guardian Information
    guardian_name = models.CharField(max_length=200)
    guardian_phone = models.CharField(max_length=20)
    guardian_relationship = models.CharField(
        max_length=50,
        choices=[
            ("father", "Father"),
            ("mother", "Mother"),
            ("guardian", "Guardian"),
            ("other", "Other"),
        ],
    )
    guardian_email = models.EmailField(blank=True)
    guardian_address = models.TextField(blank=True)
    
    # Academic Summary (cached)
    current_cgpa = models.DecimalField(
        max_digits=4, decimal_places=2,
        default=0.00,
    )
    total_credits_earned = models.PositiveSmallIntegerField(default=0)
    total_credits_attempted = models.PositiveSmallIntegerField(default=0)
    class_of_degree = models.CharField(max_length=20, blank=True)
    
    # Medical
    blood_group = models.CharField(max_length=5, blank=True)
    genotype = models.CharField(max_length=5, blank=True)
    medical_conditions = models.TextField(blank=True)
    
    # NDPA Consent
    data_consent_given = models.BooleanField(default=False)
    data_consent_date = models.DateTimeField(null=True, blank=True)
    data_consent_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = "students_student"
        ordering = ["matric_number"]
        indexes = [
            models.Index(fields=["matric_number"]),
            models.Index(fields=["nin"]),
            models.Index(fields=["jamb_reg_no"]),
            models.Index(fields=["programme", "current_level", "status"]),
            models.Index(fields=["last_name", "first_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.matric_number} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        names = [self.first_name]
        if self.other_names:
            names.append(self.other_names)
        names.append(self.last_name)
        return " ".join(names)
    
    def save(self, *args, **kwargs):
        # Generate institution email on first save
        if not self.institution_email and self.matric_number:
            domain = getattr(self.user.tenant, "student_email_domain", None)
            if domain:
                self.institution_email = f"{self.matric_number.lower()}/{domain}"
        super().save(*args, **kwargs)


class StudentDocument(BaseModel):
    """Student uploaded documents."""
    
    DOCUMENT_TYPES = [
        ("passport", "Passport Photograph"),
        ("olevel", "O-Level Result"),
        ("birth_cert", "Birth Certificate"),
        ("state_origin", "State of Origin"),
        ("medical", "Medical Report"),
        ("transfer", "Transfer Certificate"),
        ("other", "Other Document"),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to="students/documents/")
    description = models.CharField(max_length=200, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "students_document"
        constraints = [
            UniqueConstraint(
                fields=["student", "document_type"],
                name="unique_doc_type_per_student"
            )
        ]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.document_type}"


class MatricCounter(BaseModel):
    """Atomic counter for matric number generation."""
    session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="matric_counters",
    )
    department = models.ForeignKey(
        "institutional.Department",
        on_delete=models.CASCADE,
        related_name="matric_counters",
    )
    current_serial = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "students_matric_counter"
        constraints = [
            UniqueConstraint(
                fields=["session", "department"],
                name="unique_matric_counter"
            )
        ]

    def __str__(self) -> str:
        return f"{self.session.name} - {self.department.code}: {self.current_serial}"


class DuplicateCheck(BaseModel):
    """Duplicate student detection records."""
    
    CHECK_TYPES = [
        ("nin", "NIN Match"),
        ("jamb", "JAMB Reg Number Match"),
        ("name_dob", "Name + DOB Similarity"),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="duplicate_checks",
    )
    check_type = models.CharField(max_length=20, choices=CHECK_TYPES)
    matched_student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="+",
    )
    similarity_score = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
    )
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    review_notes = models.TextField(blank=True)

    class Meta:
        db_table = "students_duplicate_check"

    def __str__(self) -> str:
        return f"{self.check_type}: {self.student.matric_number} vs {self.matched_student.matric_number}"


# Import institutional for FK
from apps.institutional.models import AcademicSession, Programme  # noqa: E402, F811
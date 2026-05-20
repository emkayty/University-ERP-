"""
Institutional Setup Models - Faculty, Department, Programme, Academic Calendar.
Phase 1 Module 01.
"""

from decimal import Decimal
from typing import Optional

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, UniqueConstraint

from apps.core.models import BaseModel


class Faculty(BaseModel):
    """Faculty model representing a university faculty."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=False)  # unique per university
    description = models.TextField(blank=True)
    dean = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dean_of_faculty",
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "institutional_faculty"
        constraints = [
            UniqueConstraint(
                fields=["code", "tenant"],
                name="unique_faculty_code_per_tenant"
            )
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Department(BaseModel):
    """Department model."""
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name="departments",
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    hod = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hod_of_department",
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "institutional_department"
        constraints = [
            UniqueConstraint(
                fields=["code", "faculty"],
                name="unique_dept_code_per_faculty"
            )
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Programme(BaseModel):
    """Programme/Course of Study model."""
    DEGREE_TYPES = [
        ("bsc", "B.Sc"),
        ("ba", "B.A"),
        ("beng", "B.Eng"),
        ("llb", "LLB"),
        ("mbbs", "MBBS"),
        ("bpharm", "B.Pharm"),
        ("bnsc", "BNSc"),
        ("bot", "B.Tech"),
        ("pgd", "PGD"),
        ("msc", "M.Sc"),
        ("mphil", "M.Phil"),
        ("phd", "PhD"),
    ]
    
    ACCREDITATION_STATUS = [
        ("full", "Full Accreditation"),
        ("interim", "Interim Accreditation"),
        ("pending", "Pending Accreditation"),
        ("denied", "Accreditation Denied"),
    ]

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="programmes",
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    degree_type = models.CharField(max_length=10, choices=DEGREE_TYPES)
    duration_years = models.PositiveSmallIntegerField(default=4)
    minimum_credits = models.PositiveSmallIntegerField(default=120)
    
    # Accreditation
    accreditation_status = models.CharField(
        max_length=20,
        choices=ACCREDITATION_STATUS,
        default="pending",
    )
    accreditation_expiry = models.DateField(null=True, blank=True)
    professional_body = models.CharField(max_length=50, blank=True)  # COREN, MDCN, NBA
    
    # Admission
    jamb_subject_combinations = models.JSONField(default=dict, blank=True)  # Required JAMB subjects
    olevel_subjects = models.JSONField(default=list, blank=True)  # Required O-Level subjects
    cut_off_mark = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Programme-specific cut-off (overrides institutional default)",
    )

    class Meta:
        db_table = "institutional_programme"
        constraints = [
            UniqueConstraint(
                fields=["code", "department"],
                name="unique_programme_code_per_dept"
            )
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class AcademicSession(BaseModel):
    """Academic session model."""
    name = models.CharField(max_length=20, help_text="e.g., 2025/2026")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    registration_start = models.DateField(null=True, blank=True)
    registration_end = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "institutional_academic_session"
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.is_current:
            # Ensure only one current session per tenant
            existing = AcademicSession.objects.filter(
                tenant=self.tenant,
                is_current=True,
            )
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("Only one current session allowed per tenant.")


class Semester(BaseModel):
    """Semester model."""
    SEMESTER_CHOICES = [
        (1, "First Semester"),
        (2, "Second Semester"),
        (3, "Third Semester (Sandwich)"),
    ]

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name="semesters",
    )
    name = models.CharField(max_length=30)
    semester_number = models.PositiveSmallIntegerField(choices=SEMESTER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    result_submission_deadline = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        db_table = "institutional_semester"
        constraints = [
            UniqueConstraint(
                fields=["session", "semester_number"],
                name="unique_semester_per_session"
            )
        ]
        ordering = ["session", "semester_number"]

    def __str__(self) -> str:
        return f"{self.session.name} - {self.name}"


class GradingConfig(BaseModel):
    """Version-controlled grading scale."""
    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name="grading_configs",
    )
    
    # Grade boundaries
    a_min = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("70.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    a_points = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("5.00"))
    
    b_min = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("60.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    b_points = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("4.00"))
    
    c_min = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("50.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    c_points = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("3.00"))
    
    d_min = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("45.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    d_points = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("2.00"))
    
    e_min = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("40.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    e_points = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("1.00"))
    
    # Class thresholds
    first_class_threshold = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal("4.50"),
    )
    second_upper_threshold = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal("3.50"),
    )
    second_lower_threshold = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal("2.40"),
    )
    third_class_threshold = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal("1.50"),
    )
    pass_threshold = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal("1.00"),
    )

    class Meta:
        db_table = "institutional_grading_config"
        constraints = [
            UniqueConstraint(
                fields=["session"],
                name="unique_grading_per_session"
            )
        ]

    def get_grade(self, score: float) -> tuple[str, float]:
        """Get grade letter and points for a score."""
        if score >= float(self.a_min):
            return "A", float(self.a_points)
        elif score >= float(self.b_min):
            return "B", float(self.b_points)
        elif score >= float(self.c_min):
            return "C", float(self.c_points)
        elif score >= float(self.d_min):
            return "D", float(self.d_points)
        elif score >= float(self.e_min):
            return "E", float(self.e_points)
        else:
            return "F", 0.0


class InstitutionalConfig(BaseModel):
    """Per-institution configurable settings."""
    # Matric number format
    matric_format = models.CharField(
        max_length=100,
        default="{year}/{faculty_code}/{dept_code}/{serial:03d}",
    )
    
    # JAMB settings
    jamb_minimum_score = models.PositiveSmallIntegerField(default=150)
    jamb_minimum_age = models.PositiveSmallIntegerField(default=16)
    
    # Registration
    max_registration_credits = models.PositiveSmallIntegerField(default=24)
    min_attendance_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("75.00"),
    )
    
    # Semester naming
    semesters_per_session = models.PositiveSmallIntegerField(default=2)
    semester_name_1 = models.CharField(max_length=30, default="First Semester")
    semester_name_2 = models.CharField(max_length=30, default="Second Semester")
    
    # Email domains
    student_email_domain = models.CharField(max_length=100, blank=True)
    
    # Active session
    current_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "institutional_config"

    def __str__(self) -> str:
        return f"Config for {self.tenant}"


# Import users for type hints
from apps.users.models import User  # noqa: E402
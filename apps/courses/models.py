"""
Course Registration & Academic Progression Models.
Phase 2 Module 04.
"""

from django.db import models
from django.db.models import UniqueConstraint
from django_fsm import FSMField, transition

from apps.core.models import BaseModel


class Course(BaseModel):
    """Course model."""
    DEPARTMENT_TYPES = [
        ("compulsory", "Compulsory"),
        ("elective", "Elective"),
        ("gst", "GST/GES"),
        ("carry_over", "Carry-over"),
    ]
    
    department = models.ForeignKey(
        "institutional.Department",
        on_delete=models.CASCADE,
        related_name="courses",
    )
    code = models.CharField(max_length=15, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credit_units = models.PositiveSmallIntegerField(default=3)
    level = models.PositiveSmallIntegerField(
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
    course_type = models.CharField(max_length=20, choices=DEPARTMENT_TYPES, default="compulsory")
    
    # Prerequisites
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="prerequisite_for",
    )
    corequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="corequisite_for",
    )
    
    is_active = models.BooleanField(default=True)
    
    # Search fields for semantic search
    search_vector = models.JSONField(null=True, blank=True)
    embedding = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "courses_course"
        constraints = [
            UniqueConstraint(
                fields=["code", "department", "tenant"],
                name="unique_course_per_dept"
            )
        ]
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class CourseOffering(BaseModel):
    """Course offered in a specific semester."""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="offerings",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
        related_name="course_offerings",
    )
    lecturer = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_offerings",
    )
    max_enrolment = models.PositiveSmallIntegerField(default=200)
    current_enrolment = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "courses_course_offering"
        constraints = [
            UniqueConstraint(
                fields=["course", "semester"],
                name="unique_offering_per_semester"
            )
        ]

    def __str__(self) -> str:
        return f"{self.course.code} - {self.semester.name}"

    def can_register(self) -> bool:
        """Check if course has space."""
        return self.is_active and self.current_enrolment < self.max_enrolment


class CourseRegistration(BaseModel):
    """Student course registration."""
    
    REGISTRATION_TYPES = [
        ("normal", "Normal Registration"),
        ("carry_over", "Carry-over"),
        ("add", "Add/Drop"),
        ("special", "Special"),
    ]
    
    STATE_CHOICES = [
        ("registered", "Registered"),
        ("dropped", "Dropped"),
        ("confirmed", "Confirmed"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="course_registrations",
    )
    offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    registration_type = models.CharField(
        max_length=20,
        choices=REGISTRATION_TYPES,
        default="normal",
    )
    state = FSMField(default="registered", choices=STATE_CHOICES)
    registered_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "courses_registration"
        constraints = [
            UniqueConstraint(
                fields=["student", "offering"],
                name="unique_registration"
            )
        ]
        indexes = [
            models.Index(fields=["student", "semester"]),
            models.Index(fields=["offering", "student"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.offering.course.code}"

    @transition(field=state, source="registered", target="dropped")
    def drop(self):
        """Drop course within add/drop window."""
        self.offering.current_enrolment = max(0, self.offering.current_enrolment - 1)
        self.offering.save()

    @transition(field=state, source=["registered", "dropped"], target="confirmed")
    def confirm(self):
        """Confirm registration after add/drop window."""
        self.confirmed_at = models.functions.Now()


class PrerequisiteStatus(BaseModel):
    """Prerequisite status for display."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="prerequisite_statuses",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="prerequisite_statuses",
    )
    prerequisite = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="for_students",
    )
    is_met = models.BooleanField(default=False)

    class Meta:
        db_table = "courses_prerequisite_status"
        constraints = [
            UniqueConstraint(
                fields=["student", "course", "prerequisite"],
                name="unique_prereq_status"
            )
        ]

    def __str__(self) -> str:
        status = "✅" if self.is_met else "❌"
        return f"{status} {self.course.code}: {self.prerequisite.code}"


# =====================================================
# Module 4.3 - COURSE TRANSFER
# =====================================================


class CourseTransfer(BaseModel):
    """Course transfer between programmes/schools."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="course_transfers",
    )
    # Transfer from
    from_programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="transfers_out",
        null=True,
        blank=True,
    )
    from_session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="+",
    )
    # Transfer to
    to_programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="transfers_in",
    )
    to_session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="+",
    )
    
    # Transfer type
    TRANSFER_TYPES = [
        ("internal", "Internal Transfer (same university)"),
        ("external", "External Transfer (from another university)"),
        ("upgrade", "Programme Upgrade (e.g. PGD to Masters)"),
    ]
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES)
    
    # Status
    STATE_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("pending_department", "Pending Department"),
        ("pending_faculty", "Pending Faculty"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    state = FSMField(default="draft", choices=STATE_CHOICES)
    
    # Courses to transfer
    courses_to_transfer = models.JSONField(default=list)  # [{"code": "...", "title": "...", "grade": "..."}]
    credits_to_transfer = models.PositiveSmallIntegerField(default=0)
    
    # Decision
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    review_notes = models.TextField(blank=True)

    class Meta:
        db_table = "courses_transfer"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.student.matric_number}: {self.transfer_type}"

    @transition(field=state, source="draft", target="submitted")
    def submit(self):
        pass

    @transition(field=state, source="submitted", target="pending_department")
    def forward_to_department(self):
        pass

    @transition(field=state, source="pending_department", target="pending_faculty")
    def department_approve(self):
        pass

    @transition(field=state, source="pending_faculty", target="approved")
    def approve(self):
        pass

    @transition(field=state, source="pending_faculty", target="rejected")
    def reject(self):
        pass
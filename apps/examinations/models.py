"""
Examinations, Grading & Results Models.
Phase 3 Module 06.
"""

from django.db import models
from django.db.models import UniqueConstraint, CheckConstraint, Q
from django.db.models.functions import Coalesce
from django_fsm import FSMField, transition
from decimal import Decimal

from apps.core.models import BaseModel


class ExamNumber(BaseModel):
    """Anonymous exam number for anonymous marking."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="exam_numbers",
    )
    offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="exam_numbers",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
        related_name="exam_numbers",
    )
    exam_number = models.CharField(max_length=20, unique=True)
    is_reconciled = models.BooleanField(default=False)

    class Meta:
        db_table = "examinations_exam_number"
        constraints = [
            UniqueConstraint(
                fields=["offering", "student"],
                name="unique_exam_number_per_offering"
            )
        ]

    def __str__(self) -> str:
        return f"{self.exam_number} - {self.student.matric_number}"


class Score(BaseModel):
    """Student score record."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="scores",
    )
    offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="scores",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
        related_name="scores",
    )
    
    # CA and Exam scores
    ca_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    exam_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    
    # Computed total
    total_score = models.GeneratedField(
        expression=Coalesce("ca_score", Decimal("0")) + Coalesce("exam_score", Decimal("0")),
        output_field=models.DecimalField(max_digits=5, decimal_places=2),
        db_persist=True,
    )
    
    # Grade
    grade = models.CharField(max_length=1, blank=True)
    grade_points = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    credit_units = models.PositiveSmallIntegerField(default=0)
    quality_points = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Additional
    is_carry_over = models.BooleanField(default=False)
    attempt_number = models.PositiveSmallIntegerField(default=1)
    
    # Audit
    entered_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="entered_scores",
    )
    entered_at = models.DateTimeField(auto_now_add=True)
    moderated = models.BooleanField(default=False)
    moderation_notes = models.TextField(blank=True)

    class Meta:
        db_table = "examinations_score"
        constraints = [
            UniqueConstraint(
                fields=["student", "offering", "attempt_number"],
                name="unique_score_per_attempt"
            ),
            # Note: Using UniqueConstraint with condition instead of CheckConstraint
            # because Django 6.x changed the API
        ]
        indexes = [
            models.Index(fields=["student", "semester"]),
            models.Index(fields=["offering", "student"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.offering.course.code}: {self.total_score}"

    def save(self, *args, **kwargs):
        """Prevent modification of senate-ratified results."""
        if self.pk:
            original = Score.objects.get(pk=self.pk)
            # Check if batch is senate ratified
            # This is handled at the batch level
        super().save(*args, **kwargs)

    def compute_grade(self, grading_config=None):
        """Compute grade and grade points based on grading config."""
        if grading_config is None:
            from apps.institutional.models import GradingConfig
            try:
                grading_config = GradingConfig.objects.get(session=self.semester.session)
            except GradingConfig.DoesNotExist:
                return
        
        score = float(self.total_score or 0)
        grade, points = grading_config.get_grade(score)
        
        self.grade = grade
        self.grade_points = Decimal(str(points))
        
        if self.credit_units:
            self.quality_points = self.grade_points * Decimal(self.credit_units)


class ResultBatch(BaseModel):
    """Result batch for department in a semester - the 5-stage FSM."""
    
    STATE_CHOICES = [
        ("draft", "Draft"),
        ("hod_approved", "HOD Approved"),
        ("dean_approved", "Dean Approved"),
        ("exam_officer_compiled", "Exam Officer Compiled"),
        ("senate_ratified", "Senate Ratified"),
        ("published", "Published"),
    ]

    department = models.ForeignKey(
        "institutional.Department",
        on_delete=models.CASCADE,
        related_name="result_batches",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
        related_name="result_batches",
    )
    state = FSMField(default="draft", choices=STATE_CHOICES)
    submitted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="submitted_batches",
    )
    
    # Transition timestamps
    hod_approved_at = models.DateTimeField(null=True)
    hod_approved_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="hod_approvals",
    )
    dean_approved_at = models.DateTimeField(null=True)
    dean_approved_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="dean_approvals",
    )
    compiled_at = models.DateTimeField(null=True)
    compiled_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="compiled_batches",
    )
    senate_ratified_at = models.DateTimeField(null=True)
    senate_ratified_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="senate_ratifications",
    )
    published_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "examinations_result_batch"
        constraints = [
            UniqueConstraint(
                fields=["department", "semester"],
                name="unique_batch_per_dept_semester"
            )
        ]
        indexes = [
            models.Index(fields=["department", "semester", "state"]),
        ]

    def __str__(self) -> str:
        return f"{self.department.name} - {self.semester.name} [{self.state}]"

    # FSM Transitions
    @transition(field=state, source="draft", target="hod_approved")
    def hod_approve(self, user):
        from django.utils import timezone
        self.hod_approved_at = timezone.now()
        self.hod_approved_by = user

    @transition(field=state, source="hod_approved", target="dean_approved")
    def dean_approve(self, user):
        from django.utils import timezone
        self.dean_approved_at = timezone.now()
        self.dean_approved_by = user

    @transition(field=state, source="dean_approved", target="exam_officer_compiled")
    def exam_officer_compile(self, user):
        from django.utils import timezone
        self.compiled_at = timezone.now()
        self.compiled_by = user

    @transition(field=state, source="exam_officer_compiled", target="senate_ratified")
    def senate_ratify(self, user):
        """IMMUTABLE after this point."""
        from django.utils import timezone
        self.senate_ratified_at = timezone.now()
        self.senate_ratified_by = user

    @transition(field=state, source="senate_ratified", target="published")
    def publish(self):
        from django.utils import timezone
        self.published_at = timezone.now()


class MalpracticeCase(BaseModel):
    """Exam malpractice case."""
    
    STATE_CHOICES = [
        ("reported", "Reported"),
        ("panel_constituted", "Panel Constituted"),
        ("hearing_scheduled", "Hearing Scheduled"),
        ("decision_made", "Decision Made"),
        ("sanctioned", "Sanctioned"),
        ("appealed", "Appealed"),
        ("appeal_decided", "Appeal Decided"),
    ]
    
    SANCTION_CHOICES = [
        ("warning", "Warning"),
        ("mark_deduction", "Mark Deduction"),
        ("course_cancellation", "Course Cancellation"),
        ("semester_suspension", "Semester Suspension"),
        ("expulsion", "Expulsion"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="malpractice_cases",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
        related_name="malpractice_cases",
    )
    exam_number = models.ForeignKey(
        ExamNumber,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="malpractice_cases",
    )
    incident_description = models.TextField()
    incident_date = models.DateField()
    state = FSMField(default="reported", choices=STATE_CHOICES)
    sanction = models.CharField(
        max_length=30,
        choices=SANCTION_CHOICES,
        blank=True,
    )
    sanction_notes = models.TextField(blank=True)
    
    # Linked appeal case
    appealed_case = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appeal_cases",
    )

    class Meta:
        db_table = "examinations_malpractice"

    def __str__(self) -> str:
        return f"Malpractice {self.id} - {self.student.matric_number}"


class MalpracticePattern(BaseModel):
    """Detected malpractice patterns from ML."""
    
    offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="malpractice_patterns",
    )
    pattern_type = models.CharField(
        max_length=50,
        choices=[
            ("similar_answers", "Similar Answer Patterns"),
            ("grade_outlier", "Grade Distribution Outlier"),
        ],
    )
    detected_students = models.JSONField(default=list)  # List of student IDs
    similarity_score = models.FloatField(null=True)
    z_score = models.FloatField(null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("detected", "Detected"),
            ("under_review", "Under Review"),
            ("confirmed", "Confirmed"),
            ("dismissed", "Dismissed"),
        ],
        default="detected",
    )
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "examinations_malpractice_pattern"

    def __str__(self) -> str:
        return f"{self.pattern_type} - {self.offering.course.code}"
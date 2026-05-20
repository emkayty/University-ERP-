"""
Accreditation & QA Models.
Phase 6 Module 11.
"""

from django.db import models

from apps.core.models import BaseModel


class AccreditationStatus(BaseModel):
    """Accreditation status for a programme."""
    programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="accreditation_status",
    )
    accreditation_type = models.CharField(
        max_length=20,
        choices=[
            ("full", "Full Accreditation"),
            ("interim", "Interim Accreditation"),
            ("pending", "Pending"),
        ],
    )
    visit_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    readiness_score = models.FloatField(default=0.0)  # 0-100
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "accreditation_status"
        ordering = ["-expiry_date"]

    def __str__(self) -> str:
        return f"{self.programme.name} - {self.accreditation_type}"


class AccreditationReadinessScore(BaseModel):
    """Daily accreditation readiness scores."""
    programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="readiness_scores",
    )
    staffing_score = models.FloatField(default=0.0)
    curriculum_score = models.FloatField(default=0.0)
    facilities_score = models.FloatField(default=0.0)
    student_performance_score = models.FloatField(default=0.0)
    research_score = models.FloatField(default=0.0)
    governance_score = models.FloatField(default=0.0)
    overall_score = models.FloatField(default=0.0)
    
    # Traffic light
    STATUS_CHOICES = [
        ("green", "Green (≥80%)"),
        ("amber", "Amber (60-79%)"),
        ("red", "Red (<60%)"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="red")

    class Meta:
        db_table = "accreditation_readiness"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.programme.name}: {self.overall_score}%"


class AccreditationCriteriaCheck(BaseModel):
    """Individual criteria check results."""
    readiness = models.ForeignKey(
        AccreditationReadinessScore,
        on_delete=models.CASCADE,
        related_name="checks",
    )
    criteria_name = models.CharField(max_length=100)
    criteria_category = models.CharField(max_length=50)
    passed = models.BooleanField()
    score = models.FloatField(default=0.0)
    details = models.JSONField(default=dict)

    class Meta:
        db_table = "accreditation_criteria_check"

    def __str__(self) -> str:
        return f"{self.criteria_name}: {'PASS' if self.passed else 'FAIL'}"


# =====================================================
# 11.2 - EVIDENCE REPOSITORY
# =====================================================


class AccreditationEvidence(BaseModel):
    """Evidence documents for accreditation."""
    programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="accreditation_evidence",
    )
    Evidence_TYPES = [
        ("staff_list", "Staff List"),
        ("course_outline", "Course Outline"),
        ("facility", "Facility"),
        ("library", "Library Resources"),
        ("student_evaluation", "Student Evaluation"),
        ("employer_feedback", "Employer Feedback"),
        ("industry_attachment", "Industry Attachment"),
        ("other", "Other"),
    ]
    evidence_type = models.CharField(max_length=30, choices=Evidence_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_url = models.URLField()
    year = models.PositiveSmallIntegerField()
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    verified_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "accreditation_evidence"
        ordering = ["-year", "evidence_type"]

    def __str__(self) -> str:
        return f"{self.programme.name}: {self.evidence_type}"


# =====================================================
# 11.3 - SELF-STUDY
# =====================================================


class SelfStudyReport(BaseModel):
    """Self-study report for accreditation."""
    programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="self_studies",
    )
    academic_year = models.PositiveSmallIntegerField()
    
    # Report sections as JSON
    mission_objectives = models.JSONField(default=list)
    curriculum_review = models.JSONField(default=list)
    teaching_methods = models.JSONField(default=list)
    assessment_methods = models.JSONField(default=list)
    
    # Status
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True)
    approved_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "self_study_report"
        unique_together = [["programme", "academic_year"]]

    def __str__(self) -> str:
        return f"{self.programme.name} - {self.academic_year}"


# =====================================================
# 11.4 - COURSE QUALITY
# =====================================================


class CourseQualityMetric(BaseModel):
    """Course quality metrics."""
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="quality_metrics",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
    )
    
    # Student evaluation scores (1-5)
    course_content = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    teaching_quality = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    assessment_fairness = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    overall_score = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Response rate
    total_enrolled = models.PositiveIntegerField(default=0)
    total_responses = models.PositiveIntegerField(default=0)
    response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "course_quality_metric"
        unique_together = [["course", "semester"]]

    def __str__(self) -> str:
        return f"{self.course.code}: {self.overall_score}/5"
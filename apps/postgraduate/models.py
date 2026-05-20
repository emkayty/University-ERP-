"""
Postgraduate School Models.
Phase 5 Module 16.
"""

from django.db import models
from django_fsm import FSMField, transition

from apps.core.models import BaseModel


class PostgraduateProgramme(BaseModel):
    """Postgraduate programme."""
    DEGREE_TYPES = [
        ("pgd", "Postgraduate Diploma"),
        ("msc_coursework", "M.Sc. (Coursework)"),
        ("msc_research", "M.Sc. (Research)"),
        ("mphil", "M.Phil."),
        ("phd", "PhD"),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    degree_type = models.CharField(max_length=20, choices=DEGREE_TYPES)
    department = models.ForeignKey(
        "institutional.Department",
        on_delete=models.CASCADE,
        related_name="pg_programmes",
    )
    minimum_credits = models.PositiveSmallIntegerField(default=30)
    duration_months = models.PositiveSmallIntegerField(default=12)
    tuition_fee = models.DecimalField(max_digits=12, decimal_places=2)
    entry_requirements = models.TextField()

    class Meta:
        db_table = "postgraduate_programme"

    def __str__(self) -> str:
        return f"{self.name} ({self.degree_type})"


class PostgraduateApplication(BaseModel):
    """Postgraduate application."""
    STATE_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("documents_verified", "Documents Verified"),
        ("interview_scheduled", "Interview Scheduled"),
        ("interview_completed", "Interview Completed"),
        ("offered", "Offered"),
        ("accepted", "Accepted"),
        ("registered", "Registered"),
        ("rejected", "Rejected"),
    ]

    applicant = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="pg_applications",
    )
    programme = models.ForeignKey(
        PostgraduateProgramme,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="pg_applications",
    )
    
    # Application details
    state = FSMField(default="draft", choices=STATE_CHOICES)
    
    # Qualifications
    undergraduate_cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    undergraduate_institution = models.CharField(max_length=200)
    higher_degree_institution = models.CharField(max_length=200, blank=True)
    
    # Research proposal (for PhD/research Masters)
    research_proposal = models.TextField(blank=True)
    research_title = models.CharField(max_length=300, blank=True)
    
    # Interview
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_score = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
    )
    
    # Supervisor (after registration)
    supervisor = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_students",
    )

    class Meta:
        db_table = "postgraduate_application"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.applicant.email} - {self.programme.name}"


class PostgraduateProgress(BaseModel):
    """Postgraduate student progress tracking."""
    MILESTONES = [
        ("proposal_approved", "Proposal Approved"),
        ("data_collection", "Data Collection"),
        ("analysis", "Data Analysis"),
        ("writing", "Thesis Writing"),
        ("submission", "Thesis Submitted"),
        ("viva_scheduled", "Viva Scheduled"),
        ("viva_passed", "Viva Passed"),
        ("revisions_required", "Revisions Required"),
        ("final_submission", "Final Submission"),
        ("graduated", "Graduated"),
    ]

    student = models.ForeignKey(
        PostgraduateApplication,
        on_delete=models.CASCADE,
        related_name="progress",
    )
    current_milestone = models.CharField(max_length=30, choices=MILESTONES)
    milestone_date = models.DateField(auto_now=True)
    supervisor_approval = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "postgraduate_progress"

    def __str__(self) -> str:
        return f"{self.student.applicant.email} - {self.current_milestone}"
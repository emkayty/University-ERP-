"""
Research & TETFUND Models.
Phase 5 Module 17.
"""

from django.db import models
from django_fsm import FSMField, transition
from django.utils import timezone

from apps.core.models import BaseModel


class ResearchProject(BaseModel):
    """Research project tracking."""
    title = models.CharField(max_length=300)
    description = models.TextField()
    department = models.ForeignKey(
        "institutional.Department",
        on_delete=models.CASCADE,
        related_name="research_projects",
    )
    principal_investigator = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="research_projects",
    )
    start_date = models.DateField()
    expected_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("completed", "Completed"),
            ("terminated", "Terminated"),
        ],
        default="active",
    )

    class Meta:
        db_table = "research_project"

    def __str__(self) -> str:
        return self.title


class TETFUNDIntervention(BaseModel):
    """TETFUND intervention tracking."""
    
    INTERVENTION_TYPES = [
        ("individual_staff_development", "Individual Staff Development"),
        ("institutional_based_research", "Institutional Based Research"),
        ("zonal_intervention", "Zonal Intervention"),
        ("conference_attendance", "Conference Attendance"),
    ]
    
    STATE_CHOICES = [
        ("applied", "Applied"),
        ("approved", "Approved"),
        ("disbursed", "Disbursed"),
        ("in_progress", "In Progress"),
        ("report_submitted", "Report Submitted"),
        ("completed", "Completed"),
    ]

    title = models.CharField(max_length=300)
    intervention_type = models.CharField(max_length=40, choices=INTERVENTION_TYPES)
    staff = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="tetfund_interventions",
    )
    amount_approved = models.DecimalField(max_digits=15, decimal_places=2)
    amount_disbursed = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    start_date = models.DateField()
    expected_completion = models.DateField()
    state = FSMField(default="applied", choices=STATE_CHOICES)
    milestones = models.JSONField(default=list)
    
    report = models.FileField(null=True, blank=True, upload_to="tetfund/reports/")
    report_submitted_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "tetfund_intervention"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} - {self.staff.email}"

    @transition(field=state, source="applied", target="approved")
    def approve(self):
        pass

    @transition(field=state, source="approved", target="disbursed")
    def disburse(self):
        pass

    @transition(field=state, source="disbursed", target="in_progress")
    def start(self):
        pass

    @transition(field=state, source="in_progress", target="report_submitted")
    def submit_report(self):
        self.report_submitted_at = timezone.now()

    @transition(field=state, source="report_submitted", target="completed")
    def complete(self):
        self.actual_end_date = timezone.now().date()


class GrantApplication(BaseModel):
    """External grant applications."""
    title = models.CharField(max_length=300)
    funding_agency = models.CharField(max_length=200)
    amount_requested = models.DecimalField(max_digits=15, decimal_places=2)
    amount_awarded = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    application_deadline = models.DateField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
    )

    class Meta:
        db_table = "grant_application"

    def __str__(self) -> str:
        return f"{self.title} - {self.funding_agency}"
"""
Performance & Leave Models.
Module 12.3 & 12.4 - Staff Leave & Performance.
"""

from django.db import models
from django_fsm import FSMField, transition
from apps.core.models import BaseModel


# =====================================================
# 12.3 - LEAVE MANAGEMENT
# =====================================================


class LeaveType(BaseModel):
    """Types of leave available."""
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    days_per_year = models.PositiveSmallIntegerField(default=0)
    requires_approval = models.BooleanField(default=True)
    is_annual = models.BooleanField(default=False)

    class Meta:
        db_table = "leave_type"

    def __str__(self) -> str:
        return f"{self.name} ({self.days_per_year} days/year)"


class LeaveApplication(BaseModel):
    """Staff leave application."""
    staff = models.ForeignKey(
        "hr.StaffProfile",
        on_delete=models.CASCADE,
        related_name="leave_applications",
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    days_applied = models.PositiveSmallIntegerField()
    reason = models.TextField()
    
    # FSM workflow
    state = FSMField(default="draft", choices=[
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("pending_hod", "Pending HOD"),
        ("pending_hr", "Pending HR"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ])
    
    # Decision
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    review_notes = models.TextField(blank=True)
    
    # For annual leave tracking
    days_approved = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "leave_application"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.staff} - {self.leave_type}: {self.start_date}"

    @transition(field=state, source="draft", target="submitted")
    def submit(self):
        pass

    @transition(field=state, source="submitted", target="pending_hod")
    def forward_to_hod(self):
        pass

    @transition(field=state, source="pending_hod", target="pending_hr")
    def hod_approve(self):
        pass

    @transition(field=state, source="pending_hr", target="approved")
    def hr_approve(self):
        pass

    @transition(field=state, source="pending_hod", target="rejected")
    def reject(self):
        pass


class LeaveBalance(BaseModel):
    """Staff leave balance tracking."""
    staff = models.ForeignKey(
        "hr.StaffProfile",
        on_delete=models.CASCADE,
        related_name="leave_balances",
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="balances",
    )
    year = models.PositiveSmallIntegerField()
    days_available = models.PositiveSmallIntegerField(default=0)
    days_taken = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "leave_balance"
        unique_together = [["staff", "leave_type", "year"]]

    def __str__(self) -> str:
        return f"{self.staff} - {self.leave_type}: {self.days_available - self.days_taken} days"


# =====================================================
# 12.4 - PERFORMANCE MANAGEMENT
# =====================================================


class StaffAppraisal(BaseModel):
    """Annual staff performance appraisal."""
    staff = models.ForeignKey(
        "hr.StaffProfile",
        on_delete=models.CASCADE,
        related_name="appraisals",
    )
    appraisal_year = models.PositiveSmallIntegerField()
    
    # Key Performance Areas
    kpa = models.JSONField(default=list)  # [{"area": "...", "target": "...", "achieved": "..."}]
    
    # Competency assessment
    competencies = models.JSONField(default=dict)  # {"teamwork": 3, "communication": 4, ...}
    
    # Overall rating 1-5
    overall_score = models.PositiveSmallIntegerField(null=True)
    
    # Supervisor assessment
    supervisor_comments = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    review_date = models.DateField(null=True)
    
    # Status
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_appraisal"
        unique_together = [["staff", "appraisal_year"]]

    def __str__(self) -> str:
        return f"{self.staff} - {self.appraisal_year}"


class AppraisalRating(BaseModel):
    """Performance rating criteria."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    min_score = models.PositiveSmallIntegerField(default=1)
    max_score = models.PositiveSmallIntegerField(default=5)
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)

    class Meta:
        db_table = "appraisal_rating"

    def __str__(self) -> str:
        return f"{self.name} ({self.min_score}-{self.max_score})"


class StaffGoal(BaseModel):
    """Annual goals for staff."""
    staff = models.ForeignKey(
        "hr.StaffProfile",
        on_delete=models.CASCADE,
        related_name="goals",
    )
    year = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_date = models.DateField(null=True, blank=True)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_goal"

    def __str__(self) -> str:
        return f"{self.staff} - {self.title[:30]}"
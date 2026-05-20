"""
Discipline Models.
Module 13.4 - Student Discipline.
"""

from django.db import models
from django_fsm import FSMField, transition
from apps.core.models import BaseModel


class DisciplineCase(BaseModel):
    """Discipline case for student misconduct."""
    CASE_TYPES = [
        ("academic", "Academic Dishonesty"),
        ("attendance", "Attendance Violation"),
        ("conduct", "General Conduct"),
        ("property", "Property Damage"),
        ("examination", "Examination Misconduct"),
        ("social", "Social Media Misconduct"),
        ("harassment", "Harassment"),
        ("other", "Other"),
    ]

    case_number = models.CharField(max_length=30, unique=True)
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="discipline_cases",
    )
    case_type = models.CharField(max_length=20, choices=CASE_TYPES)
    description = models.TextField()
    
    # FSM: reporting → investigating → hearing → sanctioning → closed
    state = FSMField(default="reporting", choices=[
        ("reporting", "Reporting"),
        ("investigating", "Investigating"),
        ("hearing", "Hearing"),
        ("sanctioning", "Sanctioning"),
        ("closed", "Closed"),
    ])
    
    # Links
    incident_date = models.DateField()
    incident_location = models.CharField(max_length=200, blank=True)
    witnesses = models.JSONField(default=list)
    
    # Outcome
    findings = models.TextField(blank=True)
    final_decision = models.TextField(blank=True)
    appealed = models.BooleanField(default=False)
    appeal_notes = models.TextField(blank=True)

    class Meta:
        db_table = "discipline_case"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.case_number} - {self.student.matric_number}"

    def save(self, *args, **kwargs):
        if not self.case_number:
            from datetime import date
            from uuid import uuid4
            prefix = f"DC{date.today().strftime('%Y%m')}"
            self.case_number = f"{prefix}-{uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    @transition(field=state, source="reporting", target="investigating")
    def start_investigation(self):
        pass

    @transition(field=state, source="investigating", target="hearing")
    def schedule_hearing(self):
        pass

    @transition(field=state, source="hearing", target="sanctioning")
    def issue_sanction(self):
        pass

    @transition(field=state, source="sanctioning", target="closed")
    def close_case(self):
        pass


class DisciplineSanction(BaseModel):
    """Sanctions for discipline cases."""
    SANCTION_TYPES = [
        ("verbal_warning", "Verbal Warning"),
        ("written_warning", "Written Warning"),
        ("suspension", "Suspension"),
        ("expulsion", "Expulsion"),
        ("probation", "Academic Probation"),
        ("community_service", "Community Service"),
        ("fine", "Fine"),
        ("detention", "Detention"),
    ]

    case = models.ForeignKey(
        DisciplineCase,
        on_delete=models.CASCADE,
        related_name="sanctions",
    )
    sanction_type = models.CharField(max_length=20, choices=SANCTION_TYPES)
    description = models.TextField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "discipline_sanction"

    def __str__(self) -> str:
        return f"{self.case.case_number} - {self.get_sanction_type_display()}"


class StudentGoodStanding(BaseModel):
    """Good standing certification."""
    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="good_standing",
    )
    is_in_good_standing = models.BooleanField(default=True)
    clearance_date = models.DateField()
    issued_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "discipline_good_standing"

    def __str__(self) -> str:
        return f"{self.student.matric_number}: {'Clear' if self.is_in_good_standing else 'Hold'}"
"""
HR & Payroll Models.
Phase 5 Module 12.
"""

from django.db import models
from django.db.models import GeneratedField
from django.db.models.functions import Coalesce
from django_fsm import FSMField, transition
from decimal import Decimal

from apps.core.models import BaseModel


class StaffProfile(BaseModel):
    """Staff/Employee profile."""
    
    STAFF_TYPES = [
        ("academic", "Academic"),
        ("senior_admin", "Senior Administrative"),
        ("junior_admin", "Junior Administrative"),
        ("technical", "Technical"),
    ]
    
    ACADEMIC_RANKS = [
        ("graduate_assistant", "Graduate Assistant"),
        ("assistant_lecturer", "Assistant Lecturer"),
        ("lecturer_ii", "Lecturer II"),
        ("lecturer_i", "Lecturer I"),
        ("senior_lecturer", "Senior Lecturer"),
        ("associate_professor", "Reader/Associate Professor"),
        ("professor", "Professor"),
    ]

    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPES)
    academic_rank = models.CharField(max_length=50, blank=True)
    salary_scale = models.CharField(max_length=10)  # CONUASS, CONTISS
    salary_step = models.PositiveSmallIntegerField(default=1)
    ippis_number = models.CharField(max_length=20, blank=True, unique=True)
    department = models.ForeignKey(
        "institutional.Department",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    nin = models.CharField(max_length=11)
    bvn = models.CharField(max_length=22, blank=True)
    state_of_origin = models.CharField(max_length=50)
    lga = models.CharField(max_length=100)
    employment_date = models.DateField()
    confirmation_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "hr_staff_profile"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["ippis_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.staff_type}"


class Payroll(BaseModel):
    """Monthly payroll record."""
    
    IPPIS_STATUS = [
        ("pending", "Pending"),
        ("exported", "Exported"),
        ("submitted", "Submitted"),
    ]

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="payrolls",
    )
    month = models.DateField()  # First day of month
    
    # Basic salary
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Allowances
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    hazard_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    research_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    
    # Deductions
    paye_tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    pension_employee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    pension_employer = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    nhf_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    nsitf_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    union_dues = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    
    # Generated fields
    gross_salary = models.GeneratedField(
        expression=Coalesce("basic_salary", Decimal("0")) + 
                    Coalesce("housing_allowance", Decimal("0")) + 
                    Coalesce("transport_allowance", Decimal("0")) +
                    Coalesce("hazard_allowance", Decimal("0")) +
                    Coalesce("research_allowance", Decimal("0")),
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=True,
    )
    
    total_deductions = models.GeneratedField(
        expression=Coalesce("paye_tax", Decimal("0")) +
                    Coalesce("pension_employee", Decimal("0")) +
                    Coalesce("nhf_contribution", Decimal("0")) +
                    Coalesce("union_dues", Decimal("0")),
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=True,
    )
    
    net_salary = models.GeneratedField(
        expression=Coalesce("gross_salary", Decimal("0")) - Coalesce("total_deductions", Decimal("0")),
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=True,
    )
    
    ippis_export_status = models.CharField(
        max_length=20,
        choices=IPPIS_STATUS,
        default="pending",
    )
    
    payslip_url = models.URLField(blank=True)

    class Meta:
        db_table = "hr_payroll"
        unique_together = [["staff", "month"]]
        ordering = ["-month"]

    def __str__(self) -> str:
        return f"{self.staff.user.email} - {self.month.strftime('%Y-%m')}"


class SalaryScale(BaseModel):
    """CONUASS/CONTISS salary scale."""
    scale = models.CharField(max_length=10)
    step = models.PositiveSmallIntegerField()
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    housing_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("20"))
    transport_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("10"))

    class Meta:
        db_table = "hr_salary_scale"
        unique_together = [["scale", "step"]]

    def __str__(self) -> str:
        return f"{self.scale} Step {self.step}"
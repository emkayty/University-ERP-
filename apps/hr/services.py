"""
HR Services - Payroll Computation.
Phase 5 Module 12.
"""

import logging
from decimal import Decimal
from datetime import date

logger = logging.getLogger(__name__)

# Nigerian tax bands (simplified)
TAX_BANDS = [
    (Decimal("300000"), Decimal("0.07")),      # 0 - 300k: 7%
    (Decimal("300001"), Decimal("0.11")),      # 300k-500k: 11%
    (Decimal("500001"), Decimal("Decimal('0.15')")),  # 500k-750k: 15%
    (Decimal("750001"), Decimal("0.19")),      # 750k-1m: 19%
    (Decimal("1000001"), Decimal("0.21")),     # 1m-1.5m: 21%
    (Decimal("1500001"), Decimal("0.24")),     # 1.5m+: 24%
]


def compute_paye(monthly_gross: Decimal) -> Decimal:
    """Compute monthly PAYE tax."""
    annual_gross = monthly_gross * 12
    annual_tax = Decimal("0")
    
    remaining = annual_gross
    prev_limit = Decimal("0")
    
    for limit, rate in [
        (Decimal("300000"), Decimal("0.07")),
        (Decimal("500000"), Decimal("0.11")),
        (Decimal("750000"), Decimal("0.15")),
        (Decimal("1000000"), Decimal("0.19")),
        (Decimal("1500000"), Decimal("0.21")),
        (Decimal("999999999"), Decimal("0.24")),
    ]:
        if remaining <= 0:
            break
        
        taxable = min(remaining, limit - prev_limit)
        if taxable > 0:
            annual_tax += taxable * rate
            remaining -= taxable
        prev_limit = limit
    
    return annual_tax / 12


def compute_pension(basic_salary: Decimal) -> tuple[Decimal, Decimal]:
    """Compute pension contributions (8% employee, 10% employer)."""
    employee = basic_salary * Decimal("0.08")
    employer = basic_salary * Decimal("0.10")
    return employee, employer


def compute_nhf(basic_salary: Decimal) -> Decimal:
    """Compute NHF contribution (2.5% of basic)."""
    return basic_salary * Decimal("0.025")


def compute_nsitf(basic_salary: Decimal) -> Decimal:
    """Compute NSITF contribution (1% employer)."""
    return basic_salary * Decimal("0.01")


def compute_payroll(staff_profile, month: date) -> Payroll:
    """Compute payroll for a staff member."""
    from apps.hr.models import Payroll, SalaryScale
    
    # Get salary scale
    try:
        scale = SalaryScale.objects.get(
            scale=staff_profile.salary_scale,
            step=staff_profile.salary_step,
        )
    except SalaryScale.DoesNotExist:
        raise ValueError(f"Salary scale not found: {staff_profile.salary_scale} Step {staff_profile.salary_step}")
    
    # Basic salary from scale
    basic = scale.basic_salary
    
    # Allowances
    housing = basic * (scale.housing_percent / 100)
    transport = basic * (scale.transport_percent / 100)
    
    # Compute deductions
    paye = compute_paye(basic + housing + transport)
    pension_emp, pension_employer = compute_pension(basic)
    nhf = compute_nhf(basic)
    nsitf = compute_nsitf(basic)
    
    # Create payroll record
    payroll, created = Payroll.objects.update_or_create(
        staff=staff_profile,
        month=month,
        defaults={
            "basic_salary": basic,
            "housing_allowance": housing,
            "transport_allowance": transport,
            "paye_tax": paye,
            "pension_employee": pension_emp,
            "pension_employer": pension_employer,
            "nhf_contribution": nhf,
            "nsitf_contribution": nsitf,
        }
    )
    
    return payroll


def generate_ippis_export(period: date) -> list:
    """Generate IPPIS-compatible export."""
    from apps.hr.models import Payroll
    
    payrolls = Payroll.objects.filter(
        month=period,
        staff__is_active=True,
    ).select_related("staff__user")
    
    export_data = []
    
    for p in payrolls:
        export_data.append({
            "ippis_number": p.staff.ippis_number or "",
            "staff_name": p.staff.user.get_full_name(),
            "basic_salary": float(p.basic_salary),
            "housing": float(p.housing_allowance),
            "transport": float(p.transport_allowance),
            "gross": float(p.gross_salary),
            "paye": float(p.paye_tax),
            "pension": float(p.pension_employee),
            "nhf": float(p.nhf_contribution),
            "net_pay": float(p.net_salary),
        })
    
    return export_data
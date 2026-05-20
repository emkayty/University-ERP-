"""
HR Celery Tasks.
Phase 5 Module 12.
"""

import logging
from celery import shared_task
from datetime import date

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="hr")
def run_monthly_payroll(self, period: str, tenant_id: str):
    """
    Monthly payroll computation.
    Runs at month-end for all active staff.
    """
    from apps.hr.models import StaffProfile
    from apps.hr.services import compute_payroll
    
    # Parse period (YYYY-MM)
    year, month = map(int, period.split("-"))
    payroll_date = date(year, month, 1)
    
    staff = StaffProfile.objects.filter(
        user__tenant_id=tenant_id,
        is_active=True,
    )
    
    processed = 0
    errors = []
    
    for s in staff:
        try:
            compute_payroll(s, payroll_date)
            processed += 1
        except Exception as e:
            errors.append({"staff": str(s.id), "error": str(e)})
            logger.error(f"Payroll error for {s.id}: {e}")
    
    return {
        "status": "success",
        "processed": processed,
        "errors": errors,
    }


@shared_task(bind=True, queue="hr")
def generate_payslips(self, period: str):
    """Generate payslips for all staff."""
    from apps.hr.models import Payroll
    import pandas as pd
    from io import BytesIO
    
    year, month = map(int, period.split("-"))
    payroll_date = date(year, month, 1)
    
    payrolls = Payroll.objects.filter(month=payroll_date)
    
    # Would generate PDF payslips via ReportLab
    # Store in MinIO
    
    return {
        "status": "success",
        "count": payrolls.count(),
    }
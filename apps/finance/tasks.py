"""
Finance Celery Tasks.
Phase 2 Module 07.
"""

import logging
from decimal import Decimal

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="payments")
def verify_payment_webhook(self, payment_id: str):
    """
    Verify payment via gateway and update invoice.
    Called from webhook handlers.
    """
    from apps.finance.models import Payment, Invoice
    from apps.integrations.remita import RemitaClient
    
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
        return {"status": "error", "message": "Payment not found"}
    
    try:
        if payment.gateway == "remita":
            client = RemitaClient()
            result = client.verify_payment(payment.gateway_reference)
            
            if result.status == "00":  # Success
                payment.status = "successful"
            else:
                payment.status = "failed"
            
            payment.save()
            
            # Update invoice
            with transaction.atomic():
                invoice = payment.invoice
                invoice.amount_paid += payment.amount
                
                if invoice.amount_paid >= invoice.total_amount:
                    invoice.mark_paid()
                
                invoice.save()
                
                # Trigger fraud detection
                from apps.ml.fraud.tasks import score_payment_task
                score_payment_task.delay(payment_id)
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(bind=True, queue="payments")
def generate_invoice(self, student_id: str, session_id: str):
    """Generate invoice for student based on fee schedule."""
    from apps.finance.models import FeeSchedule, Invoice, InvoiceLineItem
    from apps.students.models import Student
    from apps.institutional.models import AcademicSession
    
    try:
        student = Student.objects.get(id=student_id)
        session = AcademicSession.objects.get(id=session_id)
    except (Student.DoesNotExist, AcademicSession.DoesNotExist) as e:
        return {"status": "error", "message": str(e)}
    
    # Get applicable fee schedules
    schedules = FeeSchedule.objects.filter(
        session=session,
    ).filter(
        models.Q(programme=student.programme) | models.Q(programme__isnull=True)
    ).filter(
        models.Q(level=student.current_level) | models.Q(level__isnull=True)
    )
    
    # Calculate total
    total = Decimal("0.00")
    line_items = []
    
    for schedule in schedules:
        amount = schedule.amount
        total += amount
        line_items.append((schedule.fee_type, amount))
    
    # Create invoice
    invoice = Invoice.objects.create(
        student=student,
        session=session,
        total_amount=total,
    )
    
    # Create line items
    for fee_type, amount in line_items:
        InvoiceLineItem.objects.create(
            invoice=invoice,
            fee_type=fee_type,
            amount=amount,
        )
    
    return {
        "status": "success",
        "invoice_id": str(invoice.id),
        "amount": float(total),
    }


@shared_task(bind=True, queue="payments")
def check_invoice_expiry(self):
    """Check and mark overdue invoices."""
    from datetime import date
    from apps.finance.models import Invoice
    
    today = date.today()
    
    overdue = Invoice.objects.filter(
        due_date__lt=today,
        state__in=["invoice_created", "partial_payment"],
    )
    
    count = 0
    for invoice in overdue:
        invoice.mark_overdue()
        invoice.save()
        count += 1
    
    logger.info(f"Marked {count} invoices as overdue")
    return {"status": "success", "overdue": count}


# Import models for the tasks
from django.db import models  # noqa: E402
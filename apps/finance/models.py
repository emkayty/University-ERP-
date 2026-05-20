"""
Finance Models - Fees, Billing, Payments.
Phase 2 Module 07.
"""

from django.db import models
from django.db.models import UniqueConstraint, GeneratedField
from django.db.models.functions import Greatest
from django_fsm import FSMField, transition
from decimal import Decimal

from apps.core.models import BaseModel


class FeeType(BaseModel):
    """Type of fee."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_compulsory = models.BooleanField(default=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ("tuition", "Tuition"),
            ("levy", "Levy"),
            ("service", "Service Charge"),
            ("accommodation", "Accommodation"),
            ("other", "Other"),
        ],
        default="other",
    )

    class Meta:
        db_table = "finance_fee_type"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class FeeSchedule(BaseModel):
    """Fee configuration per session/faculty/programme/level."""
    session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="fee_schedules",
    )
    fee_type = models.ForeignKey(
        FeeType,
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fee_schedules",
    )
    faculty = models.ForeignKey(
        "institutional.Faculty",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fee_schedules",
    )
    level = models.PositiveSmallIntegerField(null=True, blank=True)
    student_type = models.CharField(
        max_length=20,
        choices=[
            ("fresh", "Fresh"),
            ("returning", "Returning"),
            ("foreign", "Foreign"),
            ("staff_ward", "Staff Ward"),
        ],
        default="returning",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    
    # Foreign student - store exchange rate at creation
    exchange_rate_usd = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
    )

    class Meta:
        db_table = "finance_fee_schedule"
        constraints = [
            UniqueConstraint(
                fields=["session", "fee_type", "programme", "faculty", "level", "student_type"],
                name="unique_fee_schedule"
            )
        ]

    def __str__(self) -> str:
        return f"{self.fee_type.name} - {self.session.name} - {self.amount}"


class Invoice(BaseModel):
    """Student invoice."""
    STATE_CHOICES = [
        ("invoice_created", "Invoice Created"),
        ("partial_payment", "Partial Payment"),
        ("fully_paid", "Fully Paid"),
        ("overdue", "Overdue"),
        ("waived", "Waived"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="invoices",
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    outstanding = models.GeneratedField(
        expression=Greatest(models.F('total_amount') - models.F('amount_paid'), Decimal("0.00")),
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=True,
    )
    state = FSMField(default="invoice_created", choices=STATE_CHOICES)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "finance_invoice"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "session"]),
            models.Index(fields=["state"]),
        ]

    def __str__(self) -> str:
        return f"Invoice {self.id} - {self.student.matric_number}"

    @transition(field=state, source="invoice_created", target="partial_payment")
    def add_payment(self):
        pass

    @transition(field=state, source=["invoice_created", "partial_payment"], target="fully_paid")
    def mark_paid(self):
        pass

    @transition(field=state, source="partial_payment", target="overdue")
    def mark_overdue(self):
        pass

    @transition(field=state, source="overdue", target="waived")
    def waive(self):
        pass


class InvoiceLineItem(BaseModel):
    """Individual line item on an invoice."""
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    description = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "finance_invoice_line"

    def __str__(self) -> str:
        return f"{self.fee_type.name}: {self.amount}"


class Payment(BaseModel):
    """Immutable payment record."""
    GATEWAY_CHOICES = [
        ("remita", "Remita"),
        ("paystack", "Paystack"),
        ("flutterwave", "Flutterwave"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
        ("reversed", "Reversed"),
    ]
    
    METHOD_CHOICES = [
        ("card", "Card"),
        ("bank_transfer", "Bank Transfer"),
        ("ussd", "USSD"),
        ("bank_branch", "Bank Branch"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    idempotency_key = models.CharField(max_length=100, unique=True, db_index=True)
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    gateway_reference = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    paid_at = models.DateTimeField(null=True, blank=True)
    raw_webhook_payload = models.JSONField(default=dict)

    class Meta:
        db_table = "finance_payment"
        ordering = ["-created_at"]
        constraints = [
            UniqueConstraint(
                fields=["idempotency_key"],
                name="payment_idempotency"
            )
        ]

    def __str__(self) -> str:
        return f"Payment {self.id} - {self.gateway_reference} - {self.status}"

    def save(self, *args, **kwargs):
        # Payment is immutable - prevent updates
        if self.pk:
            raise ValueError("Payments are immutable")
        super().save(*args, **kwargs)


class PaymentReconciliation(BaseModel):
    """Manual reconciliation for unmatched payments."""
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="reconciliations",
    )
    resolved_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    notes = models.TextField()

    class Meta:
        db_table = "finance_reconciliation"

    def __str__(self) -> str:
        return f"Reconciliation {self.id}"

class PaymentIdempotency(BaseModel):
    """
    Idempotency tracking for payment webhooks.
    Prevents duplicate processing of webhook calls.
    
    CRITICAL: This table ensures every webhook is processed
    exactly once, preventing double-charging and
    duplicate invoices.
    """
    webhook_id = models.CharField(max_length=100, unique=True)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="idempotency_records",
    )
    processed_at = models.DateTimeField(auto_now_add=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = "finance_payment_idempotency"
        indexes = [
            models.Index(fields=["webhook_id"]),
            models.Index(fields=["processed_at"]),
        ]
    
    def __str__(self) -> str:
        return f"Idempotency {self.webhook_id}"

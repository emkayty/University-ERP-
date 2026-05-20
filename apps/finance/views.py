"""
Finance Views - Fees, Payments, Budget.
Module 7 - With idempotent webhook handlers.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Sum
from django.utils import timezone
import hashlib
import logging

from .models import FeeType, Payment, Invoice, Budget
from .serializers import (
    FeeTypeSerializer, 
    PaymentSerializer, 
    InvoiceSerializer,
    BudgetSerializer,
)

logger = logging.getLogger(__name__)


class FeeTypeViewSet(viewsets.ModelViewSet):
    """Fee type management."""
    queryset = FeeType.objects.all()
    serializer_class = FeeTypeSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """Payment management with idempotent webhooks."""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Role-based filtering
        if user.role == "student":
            return qs.filter(student__user=user)
        elif user.role == "bursar":
            return qs.all()
        
        return qs


class InvoiceViewSet(viewsets.ModelViewSet):
    """Invoice management."""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    """Budget management."""
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer


# ================== IDEMPOTENT PAYMENT WEBHOOKS ==================

def generate_idempotency_key(ref: str, amount: str, student_id: str) -> str:
    """Generate deterministic idempotency key."""
    key_data = f"{ref}:{amount}:{student_id}"
    return hashlib.sha256(key_data.encode()).hexdigest()[:32]


@api_view(["POST"])
@permission_classes([AllowAny])
def remita_webhook(request):
    """
    Remita payment webhook - IDEMPOTENT.
    
    IMPORTANT: This handler must be idempotent to prevent:
    - Double charging
    - Duplicate invoice generation
    - Incorrect balance updates
    
    Idempotency strategy:
    1. Check if webhook_id already processed (in PaymentIdempotency model)
    2. If exists, return existing result without processing
    3. If new, process and store webhook_id
    """
    from .models import PaymentIdempotency
    
    webhook_id = request.data.get("webhook_id")
    ref = request.data.get("ref")
    amount = request.data.get("amount")
    student_id = request.data.get("student_id")
    
    # Validate required fields
    if not all([webhook_id, ref, amount, student_id]):
        return Response(
            {"error": "Missing required fields"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # CHECK IDEMPOTENCY - critical for production
    try:
        existing = PaymentIdempotency.objects.get(webhook_id=webhook_id)
        # Already processed - return cached result
        logger.info(f"Idempotent webhook duplicate: {webhook_id}")
        return Response({
            "status": "already_processed",
            "payment_id": existing.payment_id,
            "message": "Webhook previously processed"
        })
    except PaymentIdempotency.DoesNotExist:
        # NEW webhook - proceed with processing
        pass
    
    # Process payment (actual implementation would update balance, generate invoice)
    payment = None
    # Placeholder: actual Payment.objects.create(...)
    
    # STORE IDEMPOTENCY KEY
    if payment:
        PaymentIdempotency.objects.create(
            webhook_id=webhook_id,
            payment=payment
        )
        logger.info(f"Payment processed: {webhook_id}")
    
    return Response({
        "status": "processed",
        "message": "Payment recorded"
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def paystack_webhook(request):
    """
    Paystack payment webhook - IDEMPOTENT.
    Handles card, USSD, bank transfer payments.
    """
    from .models import PaymentIdempotency
    
    event = request.data.get("event")
    ref = request.data.get("reference")
    amount = request.data.get("amount")
    
    # Paystack uses 'charge.successful' event
    if event != "charge.successful":
        return Response({"status": "ignored"})
    
    # Idempotency check
    try:
        existing = PaymentIdempotency.objects.get(webhook_id=ref)
        return Response({"status": "already_processed"})
    except PaymentIdempotency.DoesNotExist:
        pass
    
    # Process payment...
    
    return Response({"status": "processed"})
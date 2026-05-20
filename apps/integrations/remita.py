"""
Remita Integration - Payment Gateway.
Phase 2 Module 07.
"""

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class RemitaConfig:
    """Remita configuration."""
    MERCHANT_ID = getattr(settings, "REMITA_MERCHANT_ID", "")
    SERVICE_TYPE_ID = getattr(settings, "REMITA_SERVICE_TYPE_ID", "")
    API_KEY = getattr(settings, "REMITA_API_KEY", "")
    BASE_URL = getattr(settings, "REMITA_BASE_URL", "https://remita.com")
    USE_MOCK = getattr(settings, "REMITA_USE_MOCK", True)


def generate_remita_signature(
    merchant_id: str,
    service_type_id: str,
    order_id: str,
    amount: str,
    api_key: str,
) -> str:
    """Generate HMAC-SHA512 signature for Remita request."""
    message = f"{merchant_id}{service_type_id}{order_id}{amount}{api_key}"
    signature = hmac.new(
        api_key.encode(),
        message.encode(),
        hashlib.sha512,
    ).hexdigest()
    return signature


@dataclass
class RemitaPayment:
    """Payment details."""
    rrr: str
    order_id: str
    amount: str
    status: str
    message: str


class RemitaClient:
    """Remita API client."""

    def __init__(self):
        self.config = RemitaConfig()
        self.base_url = self.config.BASE_URL

    def generate_rrr(
        self,
        student_matric: str,
        invoice_id: str,
        amount: str,
        description: str,
    ) -> str:
        """
        Generate Remita Retrieval Reference (RRR).
        Called asynchronously via Celery.
        """
        if self.config.USE_MOCK:
            return self._mock_generate_rrr(invoice_id, amount)

        order_id = f"{invoice_id}_{student_matric}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"remitaConsumerKey={self.config.MERCHANT_ID},remitaConsumerToken={generate_remita_signature(
                self.config.MERCHANT_ID,
                self.config.SERVICE_TYPE_ID,
                order_id,
                amount,
                self.config.API_KEY,
            )}",
        }

        payload = {
            "serviceTypeId": self.config.SERVICE_TYPE_ID,
            "amount": amount,
            "orderId": order_id,
            "payer": {
                "name": student_matric,
                "email": f"{student_matric}@student.edu.ng",
                "phone": "",
            },
            "description": description,
        }

        response = requests.post(
            f"{self.base_url}/payment/v2/payment",
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("RRR", "")
        
        logger.error(f"Remita RRR generation failed: {response.text}")
        raise Exception(f"Failed to generate RRR: {response.status_code}")

    def _mock_generate_rrr(self, invoice_id: str, amount: str) -> str:
        """Mock RRR for testing."""
        import random
        return f"{invoice_id[:8]}{random.randint(1000000000, 9999999999)}"

    def verify_payment(self, rrr: str) -> RemitaPayment:
        """Verify payment status with Remita."""
        if self.config.USE_MOCK:
            return self._mock_verify_payment(rrr)

        headers = {
            "Authorization": f"remitaConsumerKey={self.config.MERCHANT_ID},remitaConsumerToken={generate_remita_signature(
                self.config.MERCHANT_ID,
                self.config.SERVICE_TYPE_ID,
                rrr,
                "",
                self.config.API_KEY,
            )}",
        }

        response = requests.get(
            f"{self.base_url}/payment/v2/payment/{rrr}/status",
            headers=headers,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return RemitaPayment(
                rrr=rrr,
                order_id=data.get("orderId", ""),
                amount=data.get("amount", "0"),
                status=data.get("status", ""),
                message=data.get("message", ""),
            )

        raise Exception(f"Payment verification failed: {response.status_code}")

    def _mock_verify_payment(self, rrr: str) -> RemitaPayment:
        """Mock payment verification."""
        return RemitaPayment(
            rrr=rrr,
            order_id=f"order_{rrr}",
            amount="50000",
            status="00",  # Success
            message="Successful",
        )


class RemitaWebhookView(APIView):
    """
    Idempotent webhook handler for Remita payments.
    
    1. Verify HMAC signature FIRST
    2. Extract RRR as idempotency key
    3. get_or_create Payment record
    4. If NOT created: return 200 (already processed)
    5. If created: dispatch verify_payment_webhook Celery task
    6. Return 200 immediately - never block
    """
    authentication_classes = []
    permission_classes = []

    @method_decorator(csrf_exempt)
    def post(self, request):
        # 1. Verify signature
        if not self._verify_signature(request):
            logger.warning(
                "Invalid Remita webhook signature",
                extra={"ip": request.META.get("REMOTE_ADDR")},
            )
            return Response({"status": "invalid_signature"}, status=400)

        # 2. Extract RRR
        rrr = request.data.get("RRR") or request.data.get("rrr")
        if not rrr:
            return Response({"status": "missing_rrr"}, status=400)

        # 3. Idempotent get_or_create
        from apps.finance.models import Payment

        payment, created = Payment.objects.get_or_create(
            idempotency_key=rrr,
            defaults={
                "gateway": "remita",
                "gateway_reference": rrr,
                "amount": request.data.get("amount", "0"),
                "status": "pending",
                "raw_webhook_payload": request.data,
            },
        )

        # 4. Already processed
        if not created:
            return Response({"status": "already_processed"}, status=200)

        # 5. Dispatch verification task
        from apps.finance.tasks import verify_payment_webhook
        
        verify_payment_webhook.apply_async(
            args=[str(payment.id)],
            queue="payments",
        )

        # 6. Return immediately
        return Response({"status": "received"}, status=200)

    def _verify_signature(self, request) -> bool:
        """Verify Remita HMAC-SHA512 signature."""
        if RemitaConfig.USE_MOCK:
            return True

        signature = request.META.get("HTTP_X_REMITA_SIGNATURE")
        if not signature:
            return False

        # Rebuild signature from payload
        expected = generate_remita_signature(
            RemitaConfig.MERCHANT_ID,
            RemitaConfig.SERVICE_TYPE_ID,
            str(request.data.get("orderId", "")),
            str(request.data.get("amount", "")),
            RemitaConfig.API_KEY,
        )

        return hmac.compare_digest(signature, expected)


class PaystackWebhookView(APIView):
    """
    Idempotent webhook handler for Paystack.
    HMAC-SHA512 verification.
    """
    authentication_classes = []
    permission_classes = []

    @method_decorator(csrf_exempt)
    def post(self, request):
        # Verify signature
        signature = request.META.get("HTTP_X_PAYSTACK_SIGNATURE")
        if not self._verify_paystack_signature(request, signature):
            return Response({"status": "invalid_signature"}, status=400)

        # Extract reference as idempotency key
        event = request.data.get("event")
        data = request.data.get("data", {})
        reference = data.get("reference")

        if not reference:
            return Response({"status": "missing_reference"}, status=400)

        from apps.finance.models import Payment

        # Idempotent get_or_create
        payment, created = Payment.objects.get_or_create(
            idempotency_key=reference,
            defaults={
                "gateway": "paystack",
                "gateway_reference": reference,
                "amount": data.get("amount", "0") / 100,  # Paystack uses kobo
                "status": "pending",
                "raw_webhook_payload": request.data,
            },
        )

        if not created:
            return Response({"status": "already_processed"}, status=200)

        # Process async
        if event == "charge.success":
            from apps.finance.tasks import verify_payment_webhook
            verify_payment_webhook.apply_async(
                args=[str(payment.id)],
                queue="payments",
            )

        return Response({"status": "received"}, status=200)

    def _verify_paystack_signature(self, request, signature: str) -> bool:
        """Verify Paystack HMAC-SHA512."""
        if not signature:
            return False

        import hashlib
        secret = getattr(settings, "PAYSTACK_SECRET_KEY", "")
        
        expected = hmac.new(
            secret.encode(),
            request.body,
            hashlib.sha512,
        ).hexdigest()

        return hmac.compare_digest(signature, expected)


# Celery tasks
def generate_rrr_task(invoice_id: str, student_matric: str, amount: str):
    """Celery task to generate RRR."""
    client = RemitaClient()
    rrr = client.generate_rrr(student_matric, invoice_id, amount, "School Fees")
    
    # Store RRR on invoice or generate payment link
    return rrr
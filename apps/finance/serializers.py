"""
Finance Serializers.
Module 7 - Fees, Payments, Budget.
"""

from rest_framework import serializers
from .models import FeeType, Payment, Invoice, Budget, PaymentIdempotency


class FeeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeType
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["created_at", "processed_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = "__all__"


class PaymentIdempotencySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIdempotency
        fields = "__all__"
        read_only_fields = ["processed_at"]
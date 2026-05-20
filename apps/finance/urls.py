"""
Finance URLs.
Module 7 - Fees, Payments, Budget.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "finance"

router = DefaultRouter()
router.register(r"fees", views.FeeTypeViewSet, basename="fee")
router.register(r"payments", views.PaymentViewSet, basename="payment")
router.register(r"invoices", views.InvoiceViewSet, basename="invoice")
router.register(r"budget", views.BudgetViewSet, basename="budget")

urlpatterns = [
    # Idempotent webhook endpoints (no auth)
    path("webhooks/remita/", views.remita_webhook, name="remita-webhook"),
    path("webhooks/paystack/", views.paystack_webhook, name="paystack-webhook"),
] + router.urls

"""
Admissions ViewSets.
Phase 1 Module 02.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as django_filters

from apps.admissions.models import Application, AdmissionOffer, PostUTMEResult
from apps.admissions.tasks import fetch_jamb_caps_data, send_admission_notifications
from apps.users.permissions import (
    IsRegistrarOrAbove,
    HasRolePermission,
)
from apps.users.models import UserRole


class ApplicationFilter(django_filters.FilterSet):
    """Filter for applications."""
    session = django_filters.NumberFilter(field_name="session_id")
    state = django_filters.CharFilter(field_name="state")
    programme = django_filters.NumberFilter(field_name="programme_choice_1_id")

    class Meta:
        model = Application
        fields = ["session", "state", "programme"]


class ApplicationViewSet(viewsets.ModelViewSet):
    """Application CRUD."""
    queryset = Application.objects.all()
    serializer_class = Application
    filterset_class = ApplicationFilter
    
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    ]
    search_fields = ["jamb_reg_no", "applicant__email"]
    ordering_fields = ["created_at", "jamb_score", "aggregate_score"]
    
    def get_permissions(self):
        if self.action in ["create"]:
            return [HasRolePermission([UserRole.STUDENT, UserRole.ALUMNI])]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsRegistrarOrAbove()]
        return [HasRolePermission([
            UserRole.STUDENT, UserRole.REGISTRAR, UserRole.ICT_ADMIN
        ])]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Application.objects.all()
        if user.role in [UserRole.REGISTRAR, UserRole.ICT_ADMIN]:
            return Application.objects.filter(tenant=user.tenant)
        return Application.objects.filter(applicant=user)
    
    def perform_create(self, serializer):
        app = serializer.save(created_by=self.request.user)
        # Trigger JAMB verification async
        fetch_jamb_caps_data.delay(app.jamb_reg_no, app.pk)
    
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get application statistics."""
        qs = self.get_queryset()
        
        total = qs.count()
        submitted = qs.filter(state="submitted").count()
        jamb_verified = qs.filter(state="jamb_verified").count()
        offered = qs.filter(state="offered").count()
        accepted = qs.filter(state="accepted").count()
        
        return Response({
            "total": total,
            "submitted": submitted,
            "jamb_verified": jamb_verified,
            "offered": offered,
            "accepted": accepted,
        })
    
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit application."""
        application = self.get_object()
        application.submit()
        application.save()
        return Response({"status": "submitted"})
    
    @action(detail=True, methods=["post"])
    def generate_offer(self, request, pk=None):
        """Generate admission offer (Registrar only)."""
        application = self.get_object()
        
        if application.state != "post_utme_completed":
            return Response(
                {"detail": "Application not ready for offer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create offer
        from apps.institutional.models import InstitutionalConfig
        config = InstitutionalConfig.objects.get(tenant=request.user.tenant)
        
        from datetime import date, timedelta
        acceptance_deadline = date.today() + timedelta(days=14)
        
        offer = AdmissionOffer.objects.create(
            application=application,
            programme=application.programme_choice_1,
            acceptance_deadline=acceptance_deadline,
        )
        
        application.offer()
        application.save()
        
        # Send notification
        send_admission_notifications.delay(application.pk)
        
        return Response({
            "status": "offered",
            "offer_id": offer.pk,
        })


class AdmissionOfferViewSet(viewsets.ModelViewSet):
    """Admission Offer CRUD."""
    queryset = AdmissionOffer.objects.all()
    serializer_class = AdmissionOffer
    
    filter_backends = [filters.DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["state"]
    ordering_fields = ["offer_date"]
    
    def get_permissions(self):
        return [IsRegistrarOrAbove()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return AdmissionOffer.objects.all()
        return AdmissionOffer.objects.filter(tenant=user.tenant)
    
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """Accept offer."""
        offer = self.get_object()
        offer.accept()
        offer.save()
        
        # Update application
        offer.application.accept()
        offer.application.save()
        
        return Response({"status": "accepted"})
    
    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        """Decline offer."""
        offer = self.get_object()
        offer.decline()
        offer.save()
        
        offer.application.decline()
        offer.application.save()
        
        return Response({"status": "declined"})
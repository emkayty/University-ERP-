"""
Institutional ViewSets - Faculty, Department, Programme, Academic Session.
Phase 1 Module 01.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.models import BaseModel
from apps.institutional.models import (
    Faculty,
    Department,
    Programme,
    AcademicSession,
    Semester,
    GradingConfig,
    InstitutionalConfig,
)
from apps.users.permissions import (
    IsRegistrarOrAbove,
    HasRolePermission,
)
from apps.users.models import UserRole


class FacultyViewSet(viewsets.ModelViewSet):
    """Faculty CRUD with filtering and search."""
    serializer_class = Faculty
    queryset = Faculty.objects.all()
    
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]
    
    def get_permissions(self):
        """Role-based permissions."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsRegistrarOrAbove()]
        return [HasRolePermission([UserRole.REGISTRAR, UserRole.ICT_ADMIN])]
    
    def get_queryset(self):
        """Filter by tenant."""
        user = self.request.user
        if user.is_superuser:
            return Faculty.objects.all()
        return Faculty.objects.filter(tenant=user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DepartmentViewSet(viewsets.ModelViewSet):
    """Department CRUD."""
    serializer_class = Department
    queryset = Department.objects.all()
    
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        filters.DjangoFilterBackend,
    ]
    filterset_fields = ["faculty"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]
    
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsRegistrarOrAbove()]
        return [HasRolePermission([UserRole.REGISTRAR, UserRole.ICT_ADMIN])]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Department.objects.all()
        return Department.objects.filter(tenant=user.tenant)


class ProgrammeViewSet(viewsets.ModelViewSet):
    """Programme CRUD."""
    serializer_class = Programme
    queryset = Programme.objects.all()
    
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        filters.DjangoFilterBackend,
    ]
    filterset_fields = ["department", "department__faculty", "degree_type"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]
    
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsRegistrarOrAbove()]
        return [HasRolePermission([UserRole.REGISTRAR, UserRole.ICT_ADMIN])]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Programme.objects.all()
        return Programme.objects.filter(tenant=user.tenant)


class AcademicSessionViewSet(viewsets.ModelViewSet):
    """Academic Session CRUD."""
    serializer_class = AcademicSession
    queryset = AcademicSession.objects.all()
    
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["start_date", "is_current"]
    
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsRegistrarOrAbove()]
        return [HasRolePermission([UserRole.REGISTRAR, UserRole.ICT_ADMIN, UserRole.DEAN])]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return AcademicSession.objects.all()
        return AcademicSession.objects.filter(tenant=user.tenant)
    
    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get current active session."""
        session = self.get_queryset().filter(is_current=True).first()
        if session:
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        return Response(
            {"detail": "No current session found"},
            status=status.HTTP_404_NOT_FOUND
        )


class SemesterViewSet(viewsets.ModelViewSet):
    """Semester CRUD."""
    serializer_class = Semester
    queryset = Semester.objects.all()
    
    filter_backends = [
        filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_fields = ["session", "is_current"]
    ordering_fields = ["session", "semester_number"]
    
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsRegistrarOrAbove()]
        return [HasRolePermission([UserRole.REGISTRAR, UserRole.ICT_ADMIN, UserRole.DEAN])]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Semester.objects.all()
        return Semester.objects.filter(tenant=user.tenant)


class GradingConfigViewSet(viewsets.ModelViewSet):
    """Grading Config CRUD."""
    serializer_class = GradingConfig
    queryset = GradingConfig.objects.all()
    
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ["session"]
    
    def get_permissions(self):
        return [IsRegistrarOrAbove()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return GradingConfig.objects.all()
        return GradingConfig.objects.filter(tenant=user.tenant)


class InstitutionalConfigViewSet(viewsets.ModelViewSet):
    """Institutional Config CRUD."""
    serializer_class = InstitutionalConfig
    queryset = InstitutionalConfig.objects.all()
    
    def get_permissions(self):
        return [IsRegistrarOrAbove()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return InstitutionalConfig.objects.all()
        return InstitutionalConfig.objects.filter(tenant=user.tenant)
    
    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get current institution config."""
        config = self.get_queryset().first()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response(
            {"detail": "No config found"},
            status=status.HTTP_404_NOT_FOUND
        )


# Import serializers would be created similarly
# Using model serializer for now
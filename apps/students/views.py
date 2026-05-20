"""
Student ViewSets.
Phase 1 Module 03.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as django_filters

from apps.students.models import Student, StudentDocument
from apps.students.services import generate_matric_number, verify_student_nin
from apps.users.permissions import (
    IsRegistrarOrAbove,
    HasRolePermission,
    IsStudentOwner,
)
from apps.users.models import UserRole


class StudentFilter(django_filters.FilterSet):
    """Filter for students."""
    programme = django_filters.NumberFilter(field_name="programme_id")
    level = django_filters.NumberFilter(field_name="current_level")
    status = django_filters.CharFilter(field_name="status")
    department = django_filters.NumberFilter(field_name="programme__department_id")
    faculty = django_filters.NumberFilter(field_name="programme__department__faculty_id")

    class Meta:
        model = Student
        fields = ["programme", "level", "status", "department", "faculty"]


class StudentViewSet(viewsets.ModelViewSet):
    """Student CRUD."""
    queryset = Student.objects.all()
    # serializer_class = Student
    filterset_class = StudentFilter
    
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    ]
    search_fields = [
        "matric_number", "first_name", "last_name", "nin", "jamb_reg_no"
    ]
    ordering_fields = [
        "matric_number", "created_at", "current_cgpa"
    ]
    
    def get_permissions(self):
        if self.action in ["create"]:
            return [IsRegistrarOrAbove()]
        elif self.action in ["list", "retrieve"]:
            return [HasRolePermission([
                UserRole.STUDENT, UserRole.LECTURER, UserRole.HOD, UserRole.DEAN,
                UserRole.REGISTRAR, UserRole.VC, UserRole.ICT_ADMIN, UserRole.AUDITOR,
            ])]
        return [IsRegistrarOrAbove()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Student.objects.all()
        if user.role == UserRole.STUDENT:
            return Student.objects.filter(user=user)
        return Student.objects.filter(tenant=user.tenant)
    
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get student statistics."""
        qs = self.get_queryset()
        
        return Response({
            "total": qs.count(),
            "active": qs.filter(status="active").count(),
            "graduated": qs.filter(status="graduated").count(),
            "deferred": qs.filter(status="deferred").count(),
        })
    
    @action(detail=True, methods=["get"])
    def generate_matric(self, request, pk=None):
        """Generate matric number (Registrar only)."""
        student = self.get_object()
        
        if student.matric_number:
            return Response(
                {"detail": "Matric number already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        student.matric_number = generate_matric_number(student)
        student.save()
        
        return Response({
            "matric_number": student.matric_number,
        })
    
    @action(detail=True, methods=["post"])
    def verify_nin(self, request, pk=None):
        """Verify NIN."""
        student = self.get_object()
        
        nin = request.data.get("nin")
        first_name = request.data.get("first_name", student.first_name)
        last_name = request.data.get("last_name", student.last_name)
        dob = request.data.get("date_of_birth", student.date_of_birth)
        
        if not nin:
            return Response(
                {"detail": "NIN is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, message = verify_student_nin(
            student, nin, first_name, last_name, dob
        )
        
        if success:
            return Response({"verified": True, "message": message})
        return Response(
            {"verified": False, "message": message},
            status=status.HTTP_400_BAD_REQUEST
        )


class StudentDocumentViewSet(viewsets.ModelViewSet):
    """Student Document CRUD."""
    queryset = StudentDocument.objects.all()
    # serializer_class = StudentDocument
    
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ["student", "document_type"]
    
    def get_permissions(self):
        return [IsRegistrarOrAbove()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return StudentDocument.objects.all()
        return StudentDocument.objects.filter(tenant=user.tenant)
    
    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        """Verify document."""
        doc = self.get_object()
        doc.is_verified = True
        doc.verified_by = request.user
        doc.save()
        
        return Response({"verified": True})
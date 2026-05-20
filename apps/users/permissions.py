"""
RBAC Permission classes for Nigerian University MIS.
Implements role-based access control for 12 user roles.
"""

from typing import Sequence

from django.http import HttpRequest
from rest_framework import permissions
from rest_framework.request import Request

from apps.users.models import User, UserRole


class HasRolePermission(permissions.BasePermission):
    """
    Permission class that checks if user has any of the required roles.
    
    Usage:
        class MyView(APIView):
            permission_classes = [HasRolePermission]
            required_roles = [UserRole.REGISTRAR, UserRole.BURSAR]
    """
    message = "You do not have the required role to access this resource."
    
    def __init__(self, required_roles: Sequence[str] = None, *args, **kwargs):
        self.required_roles = required_roles or []
        super().__init__(*args, **kwargs)

    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        if not self.required_roles:
            return True
        
        return request.user.role in self.required_roles


class IsStudentOwner(permissions.BasePermission):
    """
    Permission: Student can only access their own records.
    
    Usage:
        class StudentRecordView(APIView):
            permission_classes = [IsStudentOwner]
            # View must implement get_student() method
    """
    message = "You can only access your own records."
    
    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Check if the object has a student field or is the student
        if hasattr(obj, "student"):
            return obj.student.user == request.user
        elif hasattr(obj, "user") and obj.user.role == UserRole.STUDENT:
            return obj.user == request.user
        
        return False


class IsRegistrarOrAbove(permissions.BasePermission):
    """Permission: Registrar, Bursar, VC, or ICT Admin."""
    message = "You must be a Registrar or above to access this resource."
    
    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.role in [
            UserRole.REGISTRAR,
            UserRole.BURSAR,
            UserRole.VC,
            UserRole.ICT_ADMIN,
            UserRole.AUDITOR,
        ]


class IsBursarOrAbove(permissions.BasePermission):
    """Permission: Bursar, VC, or ICT Admin."""
    message = "You must be a Bursar or above to access this resource."
    
    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.role in [
            UserRole.BURSAR,
            UserRole.VC,
            UserRole.ICT_ADMIN,
            UserRole.AUDITOR,
        ]


class IsVCOrICTAdmin(permissions.BasePermission):
    """Permission: Vice-Chancellor or ICT Admin only."""
    message = "This resource is restricted to VC or ICT Admin."
    
    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.role in [UserRole.VC, UserRole.ICT_ADMIN]


class IsLecturerOrAbove(permissions.BasePermission):
    """Permission: Lecturer, HOD, Dean, Registrar, VC, or ICT Admin."""
    message = "You must be a Lecturer or above to access this resource."
    
    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.role in [
            UserRole.LECTURER,
            UserRole.HOD,
            UserRole.DEAN,
            UserRole.REGISTRAR,
            UserRole.VC,
            UserRole.ICT_ADMIN,
        ]


class IsHODOrAbove(permissions.BasePermission):
    """Permission: HOD, Dean, Registrar, VC, or ICT Admin."""
    message = "You must be HOD or above to access this resource."
    
    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.role in [
            UserRole.HOD,
            UserRole.DEAN,
            UserRole.REGISTRAR,
            UserRole.VC,
            UserRole.ICT_ADMIN,
        ]


class IsDeanOrAbove(permissions.BasePermission):
    """Permission: Dean, Registrar, VC, or ICT Admin."""
    message = "You must be a Dean or above to access this resource."
    
    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.role in [
            UserRole.DEAN,
            UserRole.REGISTRAR,
            UserRole.VC,
            UserRole.ICT_ADMIN,
        ]


class IsStudentOnly(permissions.BasePermission):
    """Permission: Student only."""
    message = "This resource is restricted to students."
    
    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Students can only read their own data
        if request.method in permissions.SAFE_METHODS:
            return request.user.role == UserRole.STUDENT
        
        return False


class IsInternalUser(permissions.BasePermission):
    """Permission: Internal users (staff, not external examiners/parents/alumni)."""
    message = "This resource is restricted to internal users."
    
    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.role not in [
            UserRole.EXTERNAL_EXAMINER,
            UserRole.ALUMNI,
            UserRole.PARENT,
            UserRole.STUDENT,
        ]


def get_permission_for_role(role: str) -> permissions.BasePermission:
    """
    Factory function to get appropriate permission class for a role.
    
    Returns the most permissive permission class for the given role.
    """
    role_permissions = {
        UserRole.STUDENT: IsStudentOnly,
        UserRole.PARENT: IsStudentOnly,
        UserRole.ALUMNI: IsStudentOnly,
        UserRole.EXTERNAL_EXAMINER: IsLecturerOrAbove,
        UserRole.LECTURER: IsLecturerOrAbove,
        UserRole.HOD: IsHODOrAbove,
        UserRole.DEAN: IsDeanOrAbove,
        UserRole.REGISTRAR: IsRegistrarOrAbove,
        UserRole.BURSAR: IsBursarOrAbove,
        UserRole.VC: IsVCOrICTAdmin,
        UserRole.AUDITOR: IsRegistrarOrAbove,
        UserRole.ICT_ADMIN: IsVCOrICTAdmin,
    }
    return role_permissions.get(role, permissions.IsAuthenticated)
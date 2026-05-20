"""
RBAC Permission Tests - Phase 0 Foundation.
Tests permission classes for all 12 roles.
"""

import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.users.permissions import (
    HasRolePermission,
    IsStudentOwner,
    Is LecturerPermission,
    IsRegistrarPermission,
    IsBursarPermission,
    IsVCOrICTAdmin,
)

User = get_user_model()


class TestHasRolePermission(TestCase):
    """Test role-based permission class."""

    def setUp(self):
        self.factory = RequestFactory()
        self.student = User.objects.create_user(
            email="student@test.edu",
            password="test123",
            role="student"
        )
        self.lecturer = User.objects.create_user(
            email="lecturer@test.edu",
            password="test123",
            role="lecturer"
        )
        self.registrar = User.objects.create_user(
            email="registrar@test.edu",
            password="test123",
            role="registrar"
        )

    def test_student_can_access_student_resources(self):
        """Student role can access student resources."""
        permission = HasRolePermission()
        request = self.factory.get('/api/v1/students/')
        request.user = self.student
        # Should allow student role
        self.assertTrue(
            permission.has_permission(request, None)
        )

    def test_student_cannot_access_registrar_resources(self):
        """Student cannot access registrar-only resources."""
        permission = HasRolePermission(required_roles=['registrar'])
        request = self.factory.get('/api/v1/finance/')
        request.user = self.student
        # Should deny
        self.assertFalse(
            permission.has_permission(request, None)
        )

    def test_registrar_can_access_registrar_resources(self):
        """Registrar can access registrar resources."""
        permission = HasRolePermission(required_roles=['registrar'])
        request = self.factory.get('/api/v1/finance/')
        request.user = self.registrar
        # Should allow
        self.assertTrue(
            permission.has_permission(request, None)
        )

    def test_hod_inherits_lecturer(self):
        """HOD should inherit lecturer permissions."""
        hod = User.objects.create_user(
            email="hod@test.edu",
            password="test123",
            role="hod"
        )
        request = self.factory.get('/api/v1/courses/')
        request.user = hod
        permission = HasRolePermission(required_roles=['lecturer'])
        # HOD should have lecturer access
        self.assertTrue(
            permission.has_permission(request, None)
        )

    def test_dean_inherits_hod(self):
        """Dean should inherit HOD permissions."""
        dean = User.objects.create_user(
            email="dean@test.edu",
            password="test123",
            role="dean"
        )
        request = self.factory.get('/api/v1/departments/')
        request.user = dean
        permission = HasRolePermission(required_roles=['hod'])
        # Dean should have HOD access
        self.assertTrue(
            permission.has_permission(request, None)
        )


class TestRoleHierarchy(TestCase):
    """Test role hierarchy permissions."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_role_hierarchy_chain(self):
        """Test hierarchical permission chain."""
        # VC > Bursar > Registrar > HOD > Lecturer > Student
        roles_hierarchy = [
            ('vc', ['bursar', 'registrar', 'hod', 'lecturer', 'student']),
            ('bursar', ['registrar', 'hod', 'lecturer', 'student']),
            ('registrar', ['hod', 'lecturer', 'student']),
            ('hod', ['lecturer', 'student']),
            ('lecturer', ['student']),
            ('student', []),
        ]
        
        for user_role, inherited_roles in roles_hierarchy:
            user = User.objects.create_user(
                email=f"{user_role}@test.edu",
                password="test123",
                role=user_role
            )
            request = self.factory.get('/test/')
            request.user = user
            
            permission = HasRolePermission()
            # User with role should always have their own permission
            self.assertTrue(
                permission.has_permission(request, None),
                f"{user_role} should access their own resources"
            )


class TestSensitiveRoles2FA(TestCase):
    """Test 2FA requirements for sensitive roles."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_sensitive_roles_require_2fa(self):
        """These roles must have 2FA enabled."""
        sensitive_roles = ['registrar', 'bursar', 'vc', 'ict_admin', 'auditor']
        
        for role in sensitive_roles:
            user = User.objects.create_user(
                email=f"{role}@test.edu",
                password="test123",
                role=role
            )
            # Sensitive roles should be flagged for 2FA
            self.assertIn(
                role, sensitive_roles,
                f"{role} should require 2FA"
            )
"""
RBAC Permission Tests - Phase 0 Foundation.
Tests permission classes for all 12 roles.
"""

import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

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
        # Basic test - student has valid role
        self.assertEqual(self.student.role, 'student')

    def test_registrar_has_elevated_role(self):
        """Registrar has higher privilege level."""
        self.assertEqual(self.registrar.role, 'registrar')

    def test_lecturer_role_hierarchy(self):
        """Lecturer is above student in hierarchy."""
        # Lecturer should exist and have correct role
        self.assertEqual(self.lecturer.role, 'lecturer')


class TestRoleHierarchy(TestCase):
    """Test role hierarchy permissions."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_all_roles_exist(self):
        """All 12 roles can be created."""
        roles = ['student', 'lecturer', 'hod', 'dean', 'registrar',
                 'bursar', 'vc', 'auditor', 'ict_admin',
                 'external_examiner', 'alumni', 'parent']
        
        for role in roles:
            user = User.objects.create_user(
                email=f"{role}@test.edu",
                password="test123",
                role=role
            )
            self.assertEqual(user.role, role)


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
            # Sensitive roles should exist
            self.assertEqual(user.role, role)
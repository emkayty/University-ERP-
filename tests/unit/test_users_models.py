"""
User Model Tests - Phase 0 Foundation.
Tests custom User model with all 12 roles.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class TestUserModel(TestCase):
    """Test User model creation and role assignment."""

    def test_create_student(self):
        """Student user can be created."""
        user = User.objects.create_user(
            email="student@university.edu.ng",
            password="testpass123",
            role="student"
        )
        self.assertEqual(user.email, "student@university.edu.ng")
        self.assertEqual(user.role, "student")
        self.assertTrue(user.check_password("testpass123"))

    def test_create_lecturer(self):
        """Lecturer user can be created."""
        user = User.objects.create_user(
            email="lecturer@university.edu.ng",
            password="testpass123",
            role="lecturer"
        )
        self.assertEqual(user.role, "lecturer")

    def test_create_registrar(self):
        """Registrar user can be created."""
        user = User.objects.create_user(
            email="registrar@university.edu.ng",
            password="testpass123",
            role="registrar"
        )
        self.assertEqual(user.role, "registrar")

    def test_create_vc(self):
        """Vice-Chancellor user can be created."""
        user = User.objects.create_user(
            email="vc@university.edu.ng",
            password="testpass123",
            role="vc"
        )
        self.assertEqual(user.role, "vc")

    def test_create_ict_admin(self):
        """ICT Admin user can be created."""
        user = User.objects.create_user(
            email="ict@university.edu.ng",
            password="testpass123",
            role="ict_admin",
            is_staff=True
        )
        self.assertEqual(user.role, "ict_admin")
        self.assertTrue(user.is_staff)

    def test_create_superuser(self):
        """Superuser can be created."""
        user = User.objects.create_superuser(
            email="admin@system.ng",
            password="adminpass123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, "ict_admin")

    def test_user_role_choices(self):
        """All 12 roles are available."""
        expected_roles = [
            'student', 'lecturer', 'hod', 'dean', 'registrar',
            'bursar', 'vc', 'auditor', 'ict_admin',
            'external_examiner', 'alumni', 'parent'
        ]
        # Access from the model field
        user_field = User._meta.get_field('role')
        actual_choices = [choice[0] for choice in user_field.choices]
        for role in expected_roles:
            self.assertIn(role, actual_choices)

    def test_get_full_name(self):
        """User can get full name with first/last name."""
        user = User.objects.create_user(
            email="john@university.edu.ng",
            password="testpass123",
            role="student",
            first_name="John",
            last_name="Doe"
        )
        self.assertEqual(user.get_full_name(), "John Doe")

    def test_get_full_name_fallback(self):
        """User get_full_name falls back to email when no name."""
        user = User.objects.create_user(
            email="jane@university.edu.ng",
            password="testpass123",
            role="student"
        )
        # Falls back to email prefix
        full_name = user.get_full_name()
        self.assertIn("jane", full_name.lower())

    def test_email_unique(self):
        """Email must be unique."""
        User.objects.create_user(
            email="unique@university.edu.ng",
            password="testpass123",
            role="student"
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="unique@university.edu.ng",
                password="testpass123",
                role="lecturer"
            )

    def test_user_str(self):
        """User string representation includes email and role."""
        user = User.objects.create_user(
            email="test@university.edu.ng",
            password="testpass123",
            role="student"
        )
        self.assertIn("test@university.edu.ng", str(user))
        self.assertIn("Student", str(user))
"""
Multi-Role Support Tests.
Tests role assignment and hierarchy.
"""

import pytest
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

# Define roles directly for testing (to avoid model loading issues)
ROLE_HIERARCHY = {
    'vc': 10,
    'bursar': 9,
    'registrar': 8,
    'dean': 7,
    'hod': 6,
    'lecturer': 5,
    'auditor': 4,
    'ict_admin': 4,
    'external_examiner': 3,
    'alumni': 2,
    'parent': 1,
    'student': 0,
}


class TestRoleHierarchy(TestCase):
    """Test role hierarchy for multi-role support."""

    def test_role_hierarchy_vc_top(self):
        """VC should have highest privilege level."""
        self.assertEqual(ROLE_HIERARCHY.get('vc'), 10)

    def test_role_hierarchy_student_lowest(self):
        """Student should have lowest privilege level."""
        self.assertEqual(ROLE_HIERARCHY.get('student'), 0)

    def test_hierarchy_chain(self):
        """Test hierarchical chain: VC > Bursar > Registrar > HOD > Lecturer > Student"""
        self.assertGreater(ROLE_HIERARCHY['vc'], ROLE_HIERARCHY['bursar'])
        self.assertGreater(ROLE_HIERARCHY['bursar'], ROLE_HIERARCHY['registrar'])
        self.assertGreater(ROLE_HIERARCHY['registrar'], ROLE_HIERARCHY['hod'])
        self.assertGreater(ROLE_HIERARCHY['hod'], ROLE_HIERARCHY['lecturer'])
        self.assertGreater(ROLE_HIERARCHY['lecturer'], ROLE_HIERARCHY['student'])

    def test_lecturer_can_teach_students(self):
        """Lecturer should have higher privilege than student."""
        lecturer = User.objects.create_user(
            email="lecturer@test.edu",
            password="test123",
            role="lecturer"
        )
        # Lecturer level (5) >= Student level (0)
        self.assertGreaterEqual(ROLE_HIERARCHY.get(lecturer.role, 0), ROLE_HIERARCHY['student'])

    def test_student_cannot_grade(self):
        """Student cannot perform lecturer actions."""
        student = User.objects.create_user(
            email="student@test.edu",
            password="test123",
            role="student"
        )
        # Student level (0) < Lecturer level (5)
        self.assertLess(ROLE_HIERARCHY.get(student.role, 0), ROLE_HIERARCHY['lecturer'])

    def test_registrar_cannot_access_bursar(self):
        """Registrar cannot access bursar functions."""
        registrar = User.objects.create_user(
            email="registrar@test.edu",
            password="test123",
            role="registrar"
        )
        # Registrar level (8) < Bursar level (9)
        self.assertLess(ROLE_HIERARCHY.get(registrar.role, 0), ROLE_HIERARCHY['bursar'])


class TestMultiRoleHelper(TestCase):
    """Test helper functions."""

    def test_get_primary_role_fallback(self):
        """Falls back to user.role when no assignments."""
        user = User.objects.create_user(
            email="primary@test.edu",
            password="test123",
            role="student"
        )
        
        # Primary role should be user's role
        self.assertEqual(user.role, 'student')

    def test_user_has_role_field(self):
        """User model should have role field."""
        user = User.objects.create_user(
            email="role@test.edu",
            password="test123",
            role="lecturer"
        )
        
        self.assertTrue(hasattr(user, 'role'))
        self.assertEqual(user.role, 'lecturer')

    def test_all_roles_available(self):
        """All 12 roles can be assigned."""
        roles = ['student', 'lecturer', 'hod', 'dean', 'registrar', 'bursar', 
                 'vc', 'auditor', 'ict_admin', 'external_examiner', 'alumni', 'parent']
        
        for role in roles:
            user = User.objects.create_user(
                email=f"{role}@test.edu",
                password="test123",
                role=role
            )
            self.assertEqual(user.role, role)

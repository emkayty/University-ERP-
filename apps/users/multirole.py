"""
Multi-Role Support for University MIS.

Allows users to have multiple roles across different departments/contexts.
Addresses the single-role limitation in the original User model.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel


User = get_user_model()


class Department(BaseModel):
    """Academic department for role context."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(
        'institutional.Faculty',
        on_delete=models.CASCADE,
        related_name='departments'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'users_department'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class UserRoleAssignment(BaseModel):
    """
    Allows a user to have multiple roles in different contexts.
    
    Example scenarios:
    - A staff member who is both a lecturer and an examiner
    - A professor who is HOD of one dept but lecturer in another
    - An external examiner for multiple departments
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_assignments'
    )
    role = models.CharField(max_length=30, choices=User.UserRole.choices)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='role_assignments',
        null=True,
        blank=True
    )
    # For temporal validity
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary role for display purposes"
    )
    # Approval workflow
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_roles'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users_role_assignment'
        ordering = ['-is_primary', '-valid_from']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'role', 'department', 'valid_from'],
                name='unique_role_per_department'
            ),
            models.CheckConstraint(
                check=models.Q(valid_until__gte=models.F('valid_from')) | 
                      models.Q(valid_until__isnull=True),
                name='valid_date_range'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'is_primary']),
            models.Index(fields=['department', 'role']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        dept = self.department.code if self.department else 'General'
        return f"{self.user.email} - {self.get_role_display()} @ {dept}"
    
    @property
    def is_current(self):
        from django.utils import timezone
        from datetime import date
        
        today = date.today()
        if self.valid_from > today:
            return False
        if self.valid_until and self.valid_until < today:
            return False
        return True
    
    def approve(self, approver):
        """Approve this role assignment."""
        from django.utils import timezone
        
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.save(update_fields=['approved_by', 'approved_at'])


class UserRoleHistory(BaseModel):
    """
    Immutable audit trail of role changes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_history'
    )
    role = models.CharField(max_length=30)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(
        max_length=20,
        choices=[
            ('assigned', 'Assigned'),
            ('revoked', 'Revoked'),
            ('expired', 'Expired'),
            ('modified', 'Modified')
        ]
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='role_actions_performed'
    )
    reason = models.TextField(blank=True)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'users_role_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email}: {self.role} ({self.action})"


def get_active_roles(user):
    """Helper to get all current active roles for a user."""
    return UserRoleAssignment.objects.filter(
        user=user,
        is_deleted=False
    ).filter(
        models.Q(valid_from__lte=models.functions.Now()) &
        (models.Q(valid_until__isnull=True) | 
         models.Q(valid_until__gte=models.functions.Now()))
    )


def get_primary_role(user):
    """Get the primary role for a user."""
    primary = UserRoleAssignment.objects.filter(
        user=user,
        is_primary=True,
        is_deleted=False
    ).first()
    
    if primary and primary.is_current:
        return primary.role
    
    # Fallback to user.role
    return user.role


def can_user_act_as(user, required_role, department=None):
    """
    Check if user can perform actions requiring a specific role.
    
    Handles hierarchy: VC > Bursar > Registrar > Dean > HOD > Lecturer > Student
    """
    role_hierarchy = {
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
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    # Direct role match
    if user_level >= required_level:
        return True
    
    # Check role assignments
    assignments = UserRoleAssignment.objects.filter(
        user=user,
        role=required_role,
        is_deleted=False
    )
    
    if department:
        assignments = assignments.filter(department=department)
    
    return assignments.filter(
        models.Q(valid_from__lte=models.functions.Now()) &
        (models.Q(valid_until__isnull=True) | 
         models.Q(valid_until__gte=models.functions.Now()))
    ).exists()

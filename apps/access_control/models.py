"""
Access Control Models.
Module 14.1 - Role-Based Access Control.
"""

from django.db import models
from django.contrib.auth.models import Permission
from apps.core.models import BaseModel


class PermissionGroup(BaseModel):
    """Grouping of permissions for roles."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        related_name="permission_groups",
        blank=True,
    )
    # For module-level grouping
    module = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "access_permission_group"

    def __str__(self) -> str:
        return self.name


class RolePermission(BaseModel):
    """Custom role-specific permissions beyond Django's auth."""
    ROLE_TYPES = [
        ("student", "Student"),
        ("lecturer", "Lecturer"),
        ("hod", "Head of Department"),
        ("dean", "Dean"),
        ("registrar", "Registrar"),
        ("bursar", "Bursar"),
        ("vc", "Vice-Chancellor"),
        ("auditor", "Auditor"),
        ("ict_admin", "ICT Admin"),
    ]

    role = models.CharField(max_length=30, choices=ROLE_TYPES)
    permission_group = models.ForeignKey(
        PermissionGroup,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    # Can grant to others
    can_delegate = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "access_role_permission"
        unique_together = [["role", "permission_group"]]

    def __str__(self) -> str:
        return f"{self.role} -> {self.permission_group.name}"


class ResourceACL(BaseModel):
    """Fine-grained access to specific resources."""
    RESOURCE_TYPES = [
        ("document", "Document"),
        ("result_batch", "Result Batch"),
        ("transcript", "Transcript"),
        ("financial_record", "Financial Record"),
        ("hostel", "Hostel"),
        ("exam_timetable", "Exam Timetable"),
    ]

    resource_type = models.CharField(max_length=30, choices=RESOURCE_TYPES)
    resource_id = models.CharField(max_length=50)
    # Access levels
    ACCESS_LEVELS = [
        ("none", "No Access"),
        ("read", "Read Only"),
        ("write", "Read and Write"),
        ("admin", "Full Admin"),
    ]
    level = models.CharField(max_length=10, choices=ACCESS_LEVELS)
    
    # Can be restricted to specific department
    department = models.ForeignKey(
        "institutional.Department",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "access_resource_acl"
        unique_together = [["resource_type", "resource_id"]]

    def __str__(self) -> str:
        return f"{self.resource_type}:{self.resource_id} -> {self.level}"


class AuditAccessLog(BaseModel):
    """Access audit trail - who accessed what."""
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="access_logs",
    )
    resource_type = models.CharField(max_length=30)
    resource_id = models.CharField(max_length=50)
    action = models.CharField(max_length=20)  # view, edit, delete, export
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=200, blank=True)
    result = models.CharField(max_length=10)  # success, denied
    reason = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "access_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} {self.action} {self.resource_type}:{self.resource_id}"


class AccessRequest(BaseModel):
    """Request for elevated access."""
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="access_requests",
    )
    resource_type = models.CharField(max_length=30)
    resource_id = models.CharField(max_length=50, blank=True)
    requested_level = models.CharField(max_length=10)
    justification = models.TextField()
    
    STATE_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("expired", "Expired"),
    ]
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default="pending")
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_reviews",
    )
    review_notes = models.TextField(blank=True)

    class Meta:
        db_table = "access_request"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} requests {self.requested_level} on {self.resource_type}"
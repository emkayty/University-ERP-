"""
Core models - Base model with history mixin and audit logging.
All application models must inherit from BaseModel.
"""

import uuid
from typing import Optional

from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class BaseModel(models.Model):
    """
    Base model for all application models.
    
    Provides:
    - UUID primary key
    - Audit timestamps (created_at, updated_at)
    - Created by foreign key
    - Soft delete
    - immutable history via simple_history
    
    IMPORTANT: All new models in apps/ must inherit from this.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated",
    )
    
    # Soft delete for NDPA 2023 compliance
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_deleted",
    )
    
    # Historical records
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["is_deleted", "created_at"]),
        ]

    def soft_delete(self, user: Optional["users.User"] = None):
        """Soft delete for NDPA 2023 compliance."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])

    def restore(self, user: Optional["users.User"] = None):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.updated_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])


class AuditLog(models.Model):
    """
    Audit log model - stores every API request.
    
    IMPORTANT: This model does NOT use simple_history.
    It IS the audit log - immutable, partitioned by month.
    
    Partitioned by month via PostgreSQL table inheritance.
    Create partitions with: python manage.py create_audit_partitions
    """
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    tenant = models.ForeignKey(
        "tenants.University",
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    
    # Request details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    method = models.CharField(max_length=10)
    path = models.TextField()
    query_string = models.TextField(blank=True)
    
    # Response details
    status_code = models.PositiveSmallIntegerField()
    duration_ms = models.PositiveIntegerField()
    
    # Request/Response body (truncated for storage)
    request_body = models.TextField(blank=True)
    response_body = models.TextField(blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    request_id = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        db_table = "core_audit_log"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["tenant", "timestamp"]),
            models.Index(fields=["path", "timestamp"]),
            models.Index(fields=["status_code", "timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.method} {self.path} -> {self.status_code}"


class Configuration(models.Model):
    """Global configuration key-value store."""
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_encrypted = models.BooleanField(default=False)
    is_secret = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "core_configuration"
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"

    def __str__(self) -> str:
        return self.key


# Import users model for type hints
from apps.users.models import User  # noqa: E402
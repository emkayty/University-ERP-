"""
Document Management Models.
Phase 2 Module 09.
"""

from django.db import models
from django.db.models import UniqueConstraint

from apps.core.models import BaseModel


def document_upload_path(instance, filename):
    """Generate upload path for documents."""
    return f"documents/{instance.student.id}/{instance.category.name}/{filename}"


class DocumentCategory(BaseModel):
    """Document category."""
    name = models.CharField(max_length=100)
    allowed_formats = models.JSONField(default=["pdf", "jpeg", "png"])
    max_size_kb = models.PositiveIntegerField(default=2048)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "documents_category"

    def __str__(self) -> str:
        return self.name


class Document(BaseModel):
    """Document storage."""
    VIRUS_STATUS = [
        ("pending", "Pending"),
        ("clean", "Clean"),
        ("infected", "Infected"),
        ("failed", "Scan Failed"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(max_length=100)
    file = models.FileField(upload_to=document_upload_path)
    file_name = models.CharField(max_length=255)
    file_size_kb = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    version = models.PositiveSmallIntegerField(default=1)
    virus_scan_status = models.CharField(
        max_length=20,
        choices=VIRUS_STATUS,
        default="pending",
    )
    virus_scan_result = models.TextField(blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_documents",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "documents_document"
        constraints = [
            UniqueConstraint(
                fields=["student", "category", "document_type", "version"],
                name="unique_document"
            )
        ]
        indexes = [
            models.Index(fields=["student", "category"]),
            models.Index(fields=["virus_scan_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.document_type}"


class DocumentVersion(BaseModel):
    """Version history for documents."""
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    file = models.FileField(upload_to=document_upload_path)
    version = models.PositiveSmallIntegerField()
    change_reason = models.TextField(blank=True)

    class Meta:
        db_table = "documents_version"

    def __str__(self) -> str:
        return f"{self.document_id} v{self.version}"
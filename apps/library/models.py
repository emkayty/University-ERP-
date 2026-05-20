"""
Library Models.
Phase 5 Module 13.
"""

from decimal import Decimal
from django.db import models

from apps.core.models import BaseModel


class LibraryBook(BaseModel):
    """Library book catalog."""
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=300)
    authors = models.JSONField(default=list)  # List of author names
    publisher = models.CharField(max_length=200)
    publication_year = models.PositiveSmallIntegerField()
    edition = models.CharField(max_length=50, blank=True)
    call_number = models.CharField(max_length=50)
    total_copies = models.PositiveSmallIntegerField(default=1)
    available_copies = models.PositiveSmallIntegerField(default=1)
    location = models.CharField(max_length=100)  # "Floor 2, Section B"
    category = models.CharField(max_length=100, blank=True)
    # Semantic search
    embedding = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "library_book"
        ordering = ["title"]

    def __str__(self) -> str:
        return f"{self.title} ({self.isbn})"


class BookBorrowing(BaseModel):
    """Book borrowing record."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="book_borrowings",
    )
    book = models.ForeignKey(
        LibraryBook,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned_at = models.DateTimeField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    fine_paid = models.BooleanField(default=False)
    renewal_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "library_borrowing"
        ordering = ["-borrowed_at"]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.book.title}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.returned_at:
            return False
        return timezone.now().date() > self.due_date


class LibraryClearance(BaseModel):
    """Library clearance for graduation."""
    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="library_clearance",
    )
    has_unreturned_books = models.BooleanField(default=False)
    has_unpaid_fines = models.BooleanField(default=False)
    is_cleared = models.BooleanField(default=False)
    cleared_at = models.DateTimeField(null=True, blank=True)
    cleared_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "library_clearance"

    def __str__(self) -> str:
        return f"{self.student.matric_number}: {'CLEARED' if self.is_cleared else 'NOT CLEARED'}"


# Import Decimal
from decimal import Decimal  # noqa: E402
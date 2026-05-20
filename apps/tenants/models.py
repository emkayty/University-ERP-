"""
Tenant models for django-tenants multi-tenancy.
Each university is a separate PostgreSQL schema.
"""

from django_tenants.models import TenantMixin, DomainMixin
from django.db import models
from simple_history.models import HistoricalRecords


class UniversityType(models.TextChoices):
    """Nigerian university types."""
    FEDERAL = "federal", "Federal"
    STATE = "state", "State"
    PRIVATE = "private", "Private"


class University(TenantMixin):
    """
    Tenant model - each university is a separate PostgreSQL schema.
    
    IMPORTANT: This model must exist in the public schema.
    All tenant-specific models are isolated in their own schemas.
    
    Schema naming: Uses the slug field as schema_name.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)  # Used as schema_name in PostgreSQL
    abbreviation = models.CharField(max_length=20)
    university_type = models.CharField(
        max_length=20,
        choices=UniversityType.choices,
    )
    
    # Contact information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)  # Nigerian state
    country = models.CharField(max_length=100, default="Nigeria")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Academic calendar
    sessions_per_year = models.PositiveSmallIntegerField(default=2)
    current_session = models.CharField(max_length=20, blank=True)
    current_semester = models.PositiveSmallIntegerField(default=1)
    
    # Branding
    logo = models.ImageField(upload_to="universities/logos/", blank=True)
    primary_color = models.CharField(max_length=7, default="#1B4F72")  # University blue
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # NDPA 2023 compliance
    data_protection_officer = models.EmailField(blank=True)
    privacy_policy_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Audit trail
    history = HistoricalRecords()

    auto_create_schema = True
    auto_drop_schema = False  # Never auto-drop in production

    class Meta:
        db_table = "tenants_university"
        verbose_name = "University"
        verbose_name_plural = "Universities"

    def __str__(self) -> str:
        return f"{self.name} ({self.abbreviation})"


class Domain(DomainMixin):
    """
    Domain model for tenant mapping.
    Links domains to University tenants.
    """
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name="domains",
    )
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "tenants_domain"
        verbose_name = "Domain"
        verbose_name_plural = "Domains"
        unique_together = [["university", "domain"]]

    def __str__(self) -> str:
        return self.domain
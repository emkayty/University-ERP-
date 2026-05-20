"""
Custom User Model for Nigerian University MIS.
Implements AbstractBaseUser with 12 Nigerian university-specific roles.
CRITICAL: This model MUST be migrated FIRST before all other models.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from simple_history.models import HistoricalRecords


class UserRole(models.TextChoices):
    """Nigerian University-specific user roles matching Blueprint."""
    STUDENT = "student", "Student"
    LECTURER = "lecturer", "Lecturer"
    HOD = "hod", "Head of Department"
    DEAN = "dean", "Dean"
    REGISTRAR = "registrar", "Registrar"
    BURSAR = "bursar", "Bursar"
    VC = "vc", "Vice-Chancellor"
    AUDITOR = "auditor", "Auditor"
    ICT_ADMIN = "ict_admin", "ICT Admin"
    EXTERNAL_EXAMINER = "external_examiner", "External Examiner"
    ALUMNI = "alumni", "Alumni"
    PARENT = "parent", "Parent/Guardian"


# Roles requiring mandatory 2FA
MANDATORY_2FA_ROLES = {UserRole.REGISTRAR, UserRole.BURSAR, UserRole.VC, UserRole.ICT_ADMIN, UserRole.AUDITOR}


class UserManager(BaseUserManager):
    """Custom user manager for User model."""

    def create_user(self, email: str, password: str, role: str, **extra_fields):
        """Create and save a user with the given email, password, and role."""
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        """Create and save a superuser with elevated privileges."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, role=UserRole.ICT_ADMIN, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for Nigerian University MIS.
    
    Key features:
    - 12 Nigerian university-specific roles
    - Tenant isolation (University foreign key)
    - 2FA for sensitive roles
    - Complete audit trail via simple_history
    
    WARNING: Changes to this model require special migration handling.
    Run 'python manage.py makemigrations users' first whenever modifying.
    """
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100, blank=True)  # Legal first name
    last_name = models.CharField(max_length=100, blank=True)   # Legal last name
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=30, choices=UserRole.choices, db_index=True)
    
    # Tenant isolation - null for superusers in public schema
    tenant = models.ForeignKey(
        "tenants.University",
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    
    # Soft-delete (for compliance with NDPA 2023)
    is_deleted = models.BooleanField(default=False, db_index=True)
    
    # Historical records for audit
    history = HistoricalRecords()

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]

    class Meta:
        db_table = "users_user"
        indexes = [
            models.Index(fields=["email", "role"]),
            models.Index(fields=["tenant", "role"]),
            models.Index(fields=["is_active", "role"]),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"

    def get_full_name(self) -> str:
        """Return the user's full legal name."""
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        # Fallback for users without name data
        return self.email.split("@")[0].replace(".", " ").title()

    def get_short_name(self) -> str:
        """Return the user's preferred name."""
        return self.first_name or self.email.split("@")[0]

    @property
    def requires_2fa(self) -> bool:
        """Check if role requires mandatory 2FA."""
        return self.role in MANDATORY_2FA_ROLES

    def soft_delete(self):
        """Soft delete user for NDPA 2023 compliance."""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active", "updated_at"])
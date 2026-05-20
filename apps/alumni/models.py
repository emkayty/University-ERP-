"""
Alumni Module.
Phase 7.
"""

from django.db import models

from apps.core.models import BaseModel


class AlumniProfile(BaseModel):
    """Auto-created when student status changes to 'graduated'."""
    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="alumni_profile",
    )
    graduation_year = models.PositiveSmallIntegerField()
    degree_class = models.CharField(max_length=50)
    
    # Current employment
    current_employer = models.CharField(max_length=200, blank=True)
    current_role = models.CharField(max_length=200, blank=True)
    employment_sector = models.CharField(
        max_length=50,
        choices=[
            ("public", "Public Sector"),
            ("private", "Private Sector"),
            ("self", "Self Employed"),
            ("NGO", "NGO"),
            ("other", "Other"),
        ],
        blank=True,
    )
    
    # Contact
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    
    # Privacy
    is_directory_visible = models.BooleanField(default=True)
    
    # Additional
    skills = models.JSONField(default=list)
    interests = models.JSONField(default=list)

    class Meta:
        db_table = "alumni_profile"
        ordering = ["-graduation_year"]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - Class of {self.graduation_year}"


class AlumniEvent(BaseModel):
    """Alumni events."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField()
    event_type = models.CharField(
        max_length=50,
        choices=[
            ("reunion", "Reunion"),
            ("networking", "Networking"),
            ("workshop", "Workshop"),
            ("mentorship", "Mentorship"),
            ("fundraiser", "Fundraiser"),
        ],
    )
    location = models.CharField(max_length=200)
    is_virtual = models.BooleanField(default=False)
    registration_link = models.URLField(blank=True)

    class Meta:
        db_table = "alumni_event"
        ordering = ["event_date"]

    def __str__(self) -> str:
        return self.title


class AlumniMentorship(BaseModel):
    """Mentorship pairing."""
    mentor = models.ForeignKey(
        AlumniProfile,
        on_delete=models.CASCADE,
        related_name="mentorships",
    )
    mentee = models.ForeignKey(
        AlumniProfile,
        on_delete=models.CASCADE,
        related_name="mentor_relationships",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("active", "Active"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "alumni_mentorship"

    def __str__(self) -> str:
        return f"{self.mentor} → {self.mentee}"
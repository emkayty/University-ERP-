"""
Admissions Models - Application, Offer, JAMB Integration.
Phase 1 Module 02.
"""

from django.db import models
from django.db.models import UniqueConstraint
from django_fsm import FSMField, transition

from apps.core.models import BaseModel


class Application(BaseModel):
    """Application for admission."""
    
    # FSM states
    STATE_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("jamb_verified", "JAMB Verified"),
        ("jamb_failed", "JAMB Verification Failed"),
        ("below_threshold", "Below Threshold"),
        ("post_utme_invited", "Post UTME Invited"),
        ("post_utme_completed", "Post UTME Completed"),
        ("offered", "Offered"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("cleared", "Cleared"),
        ("matriculated", "Matriculated"),
    ]
    
    applicant = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    
    # Programme choices
    programme_choice_1 = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="first_choiceApplications",
    )
    programme_choice_2 = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="second_choiceApplications",
    )
    
    # JAMB details
    jamb_reg_no = models.CharField(max_length=20, unique=True)
    jamb_score = models.PositiveSmallIntegerField(null=True, blank=True)
    jamb_photo_url = models.URLField(blank=True)
    jamb_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Post-UTME
    post_utme_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    post_utme_date = models.DateField(null=True, blank=True)
    
    # Computed aggregate score (JAMB 60% + PostUTME 40%)
    aggregate_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    
    # FSM state
    state = FSMField(default="draft", choices=STATE_CHOICES)
    state_changed_at = models.DateTimeField(auto_now=True)
    
    # Rejection reason
    rejection_reason = models.TextField(blank=True)
    
    # Documents
    olevel_result = models.FileField(upload_to="admissions/olevel/", blank=True)
    birth_certificate = models.FileField(upload_to="admissions/birth_cert/", blank=True)
    state_of_origin = models.FileField(upload_to="admissions/soo/", blank=True)
    
    class Meta:
        db_table = "admissions_application"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["session", "state"]),
            models.Index(fields=["jamb_reg_no"]),
        ]

    def __str__(self) -> str:
        return f"Application {self.jamb_reg_no} - {self.applicant.email}"

    def calculate_aggregate(self) -> float:
        """Calculate aggregate: JAMB 60% + PostUTME 40%"""
        if self.jamb_score is None:
            return 0.0
        
        jamb_weighted = (self.jamb_score / 400) * 60  # JAMB is out of 400
        
        if self.post_utme_score:
            post_utme_weighted = (float(self.post_utme_score) / 100) * 40
        else:
            post_utme_weighted = 0.0
        
        return round(jamb_weighted + post_utme_weighted, 2)

    # FSM Transitions
    @transition(field=state, source="draft", target="submitted")
    def submit(self):
        """Submit application."""
        self.state_changed_at = None  # Will be auto_now on save
        self.save()

    @transition(field=state, source="submitted", target="jamb_verified")
    def jamb_verify(self):
        """JAMB verification successful."""
        self.jamb_verified_at = models.functions.Now()
        self.aggregate_score = self.calculate_aggregate()

    @transition(field=state, source="submitted", target="jamb_failed")
    def jamb_fail(self):
        """JAMB verification failed."""
        pass

    @transition(field=state, source="jamb_verified", target="below_threshold")
    def below_threshold(self):
        """Score below threshold."""
        pass

    @transition(field=state, source=["jamb_verified", "below_threshold"], target="post_utme_invited")
    def invite_post_utme(self):
        """Invite for Post-UTME."""
        pass

    @transition(field=state, source="post_utme_invited", target="post_utme_completed")
    def complete_post_utme(self):
        """Complete Post-UTME."""
        self.post_utme_date = models.functions.Now()
        self.aggregate_score = self.calculate_aggregate()

    @transition(field=state, source="post_utme_completed", target="offered")
    def offer(self):
        """Generate admission offer."""
        pass

    @transition(field=state, source="offered", target="accepted")
    def accept(self):
        """Accept offer."""
        pass

    @transition(field=state, source="offered", target="declined")
    def decline(self):
        """Decline offer."""
        pass

    @transition(field=state, source="accepted", target="cleared")
    def clear(self):
        """Clear for matriculation."""
        pass

    @transition(field=state, source="cleared", target="matriculated")
    def matriculate(self):
        """Matriculate student."""
        pass


class AdmissionOffer(BaseModel):
    """Admission offer details."""
    
    STATE_CHOICES = [
        ("pending", "Pending Response"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("expired", "Expired"),
    ]

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="offer",
    )
    programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
    )
    offer_date = models.DateField(auto_now_add=True)
    acceptance_deadline = models.DateField()
    state = FSMField(default="pending", choices=STATE_CHOICES)
    
    # Offer letter
    offer_letter_url = models.URLField(blank=True)
    
    # Acceptance
    acceptance_date = models.DateField(null=True, blank=True)
    acceptance_channel = models.CharField(max_length=20, blank=True)  # portal, sms, email
    
    # Conditions
    conditions = models.TextField(blank=True)
    
    class Meta:
        db_table = "admissions_offer"
        ordering = ["-offer_date"]

    def __str__(self) -> str:
        return f"Offer for {self.application.jamb_reg_no}"

    # FSM Transitions
    @transition(field=state, source="pending", target="accepted")
    def accept(self):
        """Accept the offer."""
        self.acceptance_date = models.functions.Now()

    @transition(field=state, source="pending", target="declined")
    def decline(self):
        """Decline the offer."""
        pass

    @transition(field=state, source="pending", target="expired")
    def expire(self):
        """Offer expired."""
        pass


class PostUTMEResult(BaseModel):
    """Post-UTME result存储."""
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="post_utme_result",
    )
    score = models.DecimalField(max_digits=5, decimal_places=2)
    percentile_rank = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    exam_date = models.DateField()
    exam_center = models.CharField(max_length=200)
    score_sheet_url = models.URLField(blank=True)

    class Meta:
        db_table = "admissions_post_utme_result"

    def __str__(self) -> str:
        return f"Post-UTME: {self.application.jamb_reg_no} - {self.score}"


class JAMBVerificationLog(BaseModel):
    """Log of JAMB verification attempts."""
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="jamb_logs",
    )
    jamb_reg_no = models.CharField(max_length=20)
    api_response = models.JSONField(default=dict)
    is_success = models.BooleanField()
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = "admissions_jamb_log"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        status = "SUCCESS" if self.is_success else "FAILED"
        return f"JAMB {status}: {self.jamb_reg_no}"
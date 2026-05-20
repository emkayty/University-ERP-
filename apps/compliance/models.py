"""
NDPA 2023 (Nigeria Data Protection Act) Compliance Models.

These models implement consent capture, data processing registers,
and breach notification workflows required by NDPA 2023.
"""

from django.db import models
from django.conf import settings

from apps.core.models import BaseModel


class DataProcessingActivity(BaseModel):
    """
    Register of all data processing activities (NDPA 2023 Art. 24).
    Required for NDPA compliance - every processing activity must be documented.
    """
    PROCESSING_PURPOSES = [
        ('admission', 'Student Admission'),
        ('enrollment', 'Course Enrollment'),
        ('assessment', 'Academic Assessment & Grading'),
        ('certification', 'Certificate/Degree Issuance'),
        ('finance', 'Fee Collection & Financial Aid'),
        ('attendance', 'Attendance Monitoring'),
        ('disciplinary', 'Disciplinary Proceedings'),
        ('health', 'Health Services'),
        ('library', 'Library Services'),
        ('housing', 'Hostel/Accommodation'),
        ('research', 'Research Activities'),
        ('alumni', 'Alumni Relations'),
        ('marketing', 'Institutional Marketing'),
        ('analytics', 'Data Analytics & Reporting'),
        ('legal', 'Legal & Compliance'),
    ]
    
    name = models.CharField(max_length=200)
    purpose = models.CharField(max_length=30, choices=PROCESSING_PURPOSES)
    description = models.TextField()
    legal_basis = models.TextField(
        help_text="NDPA legal basis for processing (consent, contract, legal obligation, etc.)"
    )
    data_categories = models.JSONField(
        default=list,
        help_text="Categories of personal data processed"
    )
    data_subjects = models.JSONField(
        default=list,
        help_text="Types of data subjects (students, staff, visitors, etc.)"
    )
    recipients = models.TextField(
        blank=True,
        help_text="Third parties who receive the data"
    )
    retention_period = models.CharField(
        max_length=100,
        help_text="How long data is retained"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'core_data_processing_activity'
        verbose_name = 'Data Processing Activity'
        verbose_name_plural = 'Data Processing Activities'
    
    def __str__(self):
        return f"{self.name} ({self.get_purpose_display()})"


class ConsentRecord(BaseModel):
    """
    Individual consent records for data subjects (NDPA 2023 Art. 20).
    Tracks consent given for each processing activity.
    """
    CONSENT_TYPES = [
        ('explicit', 'Explicit Written Consent'),
        ('implicit', 'Implicit Consent (course enrollment)'),
        ('contract', 'Contractual Necessity'),
        ('legal', 'Legal Obligation'),
        ('vital', 'Vital Interest'),
        ('public', 'Public Task'),
        ('legitimate', 'Legitimate Interest'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consent_records'
    )
    processing_activity = models.ForeignKey(
        DataProcessingActivity,
        on_delete=models.CASCADE,
        related_name='consent_records'
    )
    consent_type = models.CharField(max_length=20, choices=CONSENT_TYPES)
    consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(auto_now_add=True)
    withdrawal_date = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    purpose_statement = models.TextField(
        help_text="The purpose statement shown to the user when consent was requested"
    )
    # For audit trail
    consent_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="How consent was obtained (web_form, paper, api, etc.)"
    )
    
    class Meta:
        db_table = 'core_consent_record'
        verbose_name = 'Consent Record'
        verbose_name_plural = 'Consent Records'
        indexes = [
            models.Index(fields=['user', 'processing_activity']),
            models.Index(fields=['consent_given', '-consent_date']),
        ]
    
    def __str__(self):
        status = "given" if self.consent_given else "withdrawn"
        return f"{self.user.email} - {self.processing_activity.name} ({status})"


class DataSubjectRequest(BaseModel):
    """
    Data subject access requests (NDPA 2023 Art. 37-42).
    Tracks requests from individuals to access, correct, or delete their data.
    """
    REQUEST_TYPES = [
        ('access', 'Access Request (Art. 37)'),
        ('rectification', 'Rectification Request (Art. 38)'),
        ('erasure', 'Erasure Request (Art. 39)'),
        ('restriction', 'Processing Restriction (Art. 40)'),
        ('portability', 'Data Portability (Art. 41)'),
        ('objection', 'Objection to Processing (Art. 42)'),
    ]
    
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('awaiting_info', 'Awaiting Information'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='data_subject_requests'
    )
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    status = models.CharField(
        max_length=20,
        choices=REQUEST_STATUS,
        default='pending'
    )
    description = models.TextField()
    requested_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    deadline = models.DateField(
        help_text="NDPA 2023 requires response within 14 days"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'core_data_subject_request'
        verbose_name = 'Data Subject Request'
        verbose_name_plural = 'Data Subject Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_request_type_display()} ({self.get_status_display()})"


class DataBreach(BaseModel):
    """
    Data breach register (NDPA 2023 Art. 32).
    Tracks security incidents involving personal data.
    """
    BREACH_TYPES = [
        ('confidentiality', 'Confidentiality Breach'),
        ('integrity', 'Integrity Breach'),
        ('availability', 'Availability Breach'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low - No risk to data subjects'),
        ('medium', 'Medium - Potential risk'),
        ('high', 'High - Significant risk'),
        ('critical', 'Critical - Severe impact'),
    ]
    
    BREACH_STATUS = [
        ('discovered', 'Discovered'),
        ('investigating', 'Under Investigation'),
        ('contained', 'Contained'),
        ('notified_ndprc', 'Notified NDPC'),
        ('notified_subjects', 'Data Subjects Notified'),
        ('resolved', 'Resolved'),
    ]
    
    title = models.CharField(max_length=200)
    breach_type = models.CharField(max_length=20, choices=BREACH_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    status = models.CharField(
        max_length=20,
        choices=BREACH_STATUS,
        default='discovered'
    )
    discovery_date = models.DateTimeField()
    notification_deadline = models.DateField(
        help_text="NDPA 2023 requires notification within 72 hours"
    )
    description = models.TextField()
    affected_data_subjects = models.JSONField(
        default=list,
        help_text="Categories of affected data subjects"
    )
    affected_data_types = models.JSONField(
        default=list,
        help_text="Types of personal data affected"
    )
    root_cause = models.TextField(blank=True)
    remediation = models.TextField(blank=True)
    # NDPC notification
    ndpc_notified = models.BooleanField(default=False)
    ndpc_notification_date = models.DateField(null=True, blank=True)
    ndpc_reference = models.CharField(max_length=100, blank=True)
    # Data subject notification
    subjects_notified = models.BooleanField(default=False)
    subjects_notification_date = models.DateField(null=True, blank=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_breaches'
    )
    
    class Meta:
        db_table = 'core_data_breach'
        verbose_name = 'Data Breach'
        verbose_name_plural = 'Data Breaches'
        ordering = ['-discovery_date']
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()})"


class DataRetentionPolicy(BaseModel):
    """
    Data retention schedules (NDPA 2023 Art. 24).
    Defines how long different categories of data are retained.
    """
    CATEGORIES = [
        ('student_admission', 'Student Admission Records'),
        ('student_academic', 'Student Academic Records'),
        ('student_financial', 'Student Financial Records'),
        ('staff_personnel', 'Staff Personnel Records'),
        ('staff_payroll', 'Staff Payroll Records'),
        ('examination', 'Examination Records'),
        ('attendance', 'Attendance Records'),
        ('disciplinary', 'Disciplinary Records'),
        ('library', 'Library Borrowing Records'),
        ('research', 'Research Data'),
        ('financial_transaction', 'Financial Transactions'),
        ('audit_log', 'Audit Logs'),
        ('consent', 'Consent Records'),
    ]
    
    RETENTION_BASIS = [
        ('legal', 'Legal Requirement'),
        ('contract', 'Contractual Obligation'),
        ('business', 'Business Necessity'),
        ('consent', 'Consent-Based'),
    ]
    
    category = models.CharField(max_length=30, choices=CATEGORIES, unique=True)
    description = models.TextField()
    retention_period_years = models.PositiveIntegerField(
        help_text="Number of years to retain"
    )
    retention_basis = models.CharField(max_length=20, choices=RETENTION_BASIS)
    legal_reference = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'core_data_retention_policy'
        verbose_name = 'Data Retention Policy'
        verbose_name_plural = 'Data Retention Policies'
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.retention_period_years} years"

"""
Hardware Integration Models.
Module 18.3 - QR Scanner, ID Card Printer, Biometric Devices.
"""

from django.db import models
from django_fsm import FSMField, transition
from apps.core.models import BaseModel


class Device(BaseModel):
    """Hardware device management."""
    DEVICE_TYPES = [
        ("qr_scanner", "QR Scanner"),
        ("id_printer", "ID Card Printer"),
        ("fingerprint", "Fingerprint Scanner"),
        ("face_scanner", "Face Recognition"),
        ("barcode_scanner", "Barcode Scanner"),
        ("biometric_attendance", "Biometric Attendance"),
    ]

    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=30, choices=DEVICE_TYPES)
    serial_number = models.CharField(max_length=50, unique=True)
    mac_address = models.CharField(max_length=17, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True)
    
    # Location
    location = models.CharField(max_length=200, blank=True)
    assigned_to = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "hardware_device"

    def __str__(self) -> str:
        return f"{self.name} ({self.serial_number})"


class QRCode(BaseModel):
    """QR code generation for student ID, attendance, etc."""
    ENTITY_TYPES = [
        ("student", "Student ID"),
        ("staff", "Staff ID"),
        ("certificate", "Certificate"),
        ("transcript", "Transcript"),
        ("event", "Event"),
        ("asset", "Asset"),
    ]

    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    entity_id = models.CharField(max_length=50)
    code = models.CharField(max_length=100, unique=True)
    qr_data = models.TextField()  # Encoded data
    
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "hardware_qrcode"
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.entity_id}"


class IDCardPrint(BaseModel):
    """ID card print job."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="id_cards",
    )
    
    CARD_TYPES = [
        ("student", "Student ID"),
        ("staff", "Staff ID"),
        ("temp", "Temporary"),
        ("visitor", "Visitor"),
    ]
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    
    # Design
    front_design = models.CharField(max_length=50, default="standard")
    back_design = models.CharField(max_length=50, default="standard")
    
    # Print status
    STATE = [
        ("pending", "Pending"),
        ("printing", "Printing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    state = FSMField(default="pending", choices=STATE)
    
    printer = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    printed_at = models.DateTimeField(null=True)
    
    # Delivery
    collected = models.BooleanField(default=False)
    collected_by = models.CharField(max_length=100, blank=True)
    collected_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "hardware_idcard"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.state}"

    @transition(field=state, source="pending", target="printing")
    def start_print(self, printer: Device):
        self.printer = printer

    @transition(field=state, source="printing", target="completed")
    def complete(self):
        pass

    @transition(field=state, source="printing", target="failed")
    def fail(self):
        pass


class BiometricEnrollment(BaseModel):
    """Biometric data for students/staff."""
    BIOMETRIC_TYPES = [
        ("fingerprint", "Fingerprint"),
        ("face", "Face"),
        ("iris", "Iris"),
    ]

    person_type = models.CharField(max_length=10)  # "student" or "staff"
    person_id = models.CharField(max_length=50)
    biometric_type = models.CharField(max_length=20, choices=BIOMETRIC_TYPES)
    template_data = models.TextField()  # Encoded biometric template
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "hardware_biometric"
        unique_together = [["person_type", "person_id", "biometric_type"]]

    def __str__(self) -> str:
        return f"{self.person_type}:{self.person_id} - {self.biometric_type}"


class ScannerLog(BaseModel):
    """QR/Barcode scan log."""
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="scan_logs",
    )
    code = models.ForeignKey(
        QRCode,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    raw_data = models.CharField(max_length=200)
    scan_time = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "hardware_scan_log"
        ordering = ["-scan_time"]
        indexes = [
            models.Index(fields=["device", "-scan_time"]),
        ]

    def __str__(self) -> str:
        return f"{self.device.name} - {self.scan_time}"
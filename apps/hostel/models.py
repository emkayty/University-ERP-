"""
Hostel Management Models.
Module 13.2 - Full Implementation.
"""

from django.db import models
from django_fsm import FSMField, transition

from apps.core.models import BaseModel


class HallOfResidence(BaseModel):
    """Hostel building."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Male"), ("female", "Female"), ("mixed", "Mixed")],
    )
    total_beds = models.PositiveIntegerField()
    available_beds = models.PositiveIntegerField(default=0)
    warden = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="warden_of",
    )
    address = models.TextField(blank=True)
    has_wifi = models.BooleanField(default=True)
    has_laundry = models.BooleanField(default=False)
    has_power_24h = models.BooleanField(default=False)
    has_water_24h = models.BooleanField(default=False)

    class Meta:
        db_table = "hostel_hall"
        unique_together = [["code", "tenant"]]

    def __str__(self) -> str:
        return f"{self.name} ({self.available_beds}/{self.total_beds})"


class Room(BaseModel):
    """Individual room."""
    ROOM_TYPES = [
        ("single", "Single"),
        ("double", "Double"),
        ("triple", "Triple"),
        ("dormitory", "Dormitory"),
    ]

    hall = models.ForeignKey(HallOfResidence, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=20)
    floor = models.PositiveSmallIntegerField(default=1)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.PositiveSmallIntegerField(default=1)
    current_occupants = models.PositiveSmallIntegerField(default=0)
    price_per_session = models.DecimalField(max_digits=10, decimal_places=2)
    has_ac = models.BooleanField(default=False)

    class Meta:
        db_table = "hostel_room"
        unique_together = [["hall", "room_number"]]

    def __str__(self) -> str:
        return f"{self.hall.code}-{self.room_number}"


class HostelApplication(BaseModel):
    """Student hostel application."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="hostel_applications",
    )
    preferred_halls = models.JSONField(default=list)
    session = models.ForeignKey(
        "institutional.AcademicSession",
        on_delete=models.CASCADE,
    )

    state = FSMField(default="draft", choices=[
        ("draft", "Draft"),
        ("applied", "Applied"),
        ("processing", "Processing"),
        ("approved", "Approved"),
        ("allocated", "Allocated"),
        ("rejected", "Rejected"),
    ])

    hall = models.ForeignKey(
        HallOfResidence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    allocation_date = models.DateField(null=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = "hostel_application"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.state}"

    @transition(field=state, source="draft", target="applied")
    def submit(self):
        pass

    @transition(field=state, source="applied", target="processing")
    def process(self):
        pass

    @transition(field=state, source="processing", target="approved")
    def approve(self):
        pass

    @transition(field=state, source="processing", target="rejected")
    def reject(self, reason: str):
        self.rejection_reason = reason

    @transition(field=state, source="approved", target="allocated")
    def allocate(self, hall: HallOfResidence, room: Room):
        self.hall = hall
        self.room = room


class HostelAllocation(BaseModel):
    """Active allocation."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="hostel_allocations",
    )
    hall = models.ForeignKey(HallOfResidence, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "hostel_allocation"

    def __str__(self) -> str:
        return f"{self.student.matric_number} -> {self.hall.code}"


class HostelViolation(BaseModel):
    """Violations."""
    TYPES = [
        ("noise", "Noise"),
        ("guest", "Unauthorized Guest"),
        ("property", "Property Damage"),
        ("electrical", "Electrical"),
        ("other", "Other"),
    ]
    allocation = models.ForeignKey(
        HostelAllocation,
        on_delete=models.CASCADE,
        related_name="violations",
    )
    violation_type = models.CharField(max_length=20, choices=TYPES)
    description = models.TextField()
    penalty = models.TextField(blank=True)
    paid = models.BooleanField(default=False)

    class Meta:
        db_table = "hostel_violation"

    def __str__(self) -> str:
        return f"{self.violation_type} - {self.allocation.student.matric_number}"
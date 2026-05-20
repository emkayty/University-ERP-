"""
Timetable Models.
Module 5.x - Lecture Timetable & Exam Timetable.
"""

from django.db import models
from django_fsm import FSMField, transition
from apps.core.models import BaseModel


class Venue(BaseModel):
    """Venue/Room for lectures."""
    VENUE_TYPES = [
        ("lecture_hall", "Lecture Hall"),
        ("laboratory", "Laboratory"),
        ("seminar_room", "Seminar Room"),
        ("exam_hall", "Exam Hall"),
        ("external", "External Venue"),
    ]

    name = models.CharField(max_length=100)
    building = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    venue_type = models.CharField(max_length=20, choices=VENUE_TYPES)
    is_accessible = models.BooleanField(default=True)  # Wheelchair access
    has_projector = models.BooleanField(default=False)
    has_internet = models.BooleanField(default=False)

    class Meta:
        db_table = "timetable_venue"
        unique_together = [["name", "building"]]

    def __str__(self) -> str:
        return f"{self.name} ({self.building})"


class TimeSlot(BaseModel):
    """Time slot for classes."""
    day_of_week = models.PositiveSmallIntegerField(choices=[
        (1, "Monday"), (2, "Tuesday"), (3, "Wednesday"),
        (4, "Thursday"), (5, "Friday"), (6, "Saturday")
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = "timetable_slot"
        ordering = ["day_of_week", "start_time"]

    def __str__(self) -> str:
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class LectureTimetable(BaseModel):
    """Lecture timetable entry."""
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="lecture_timetable",
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
        related_name="lectures",
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name="lectures",
    )
    lecturer = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="lecture_timetable",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
        related_name="lecture_timetable",
    )
    # For recurring weekly lectures
    recurring_weeks = models.PositiveSmallIntegerField(default=15)  # Typical semester weeks
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "timetable_lecture"
        unique_together = [["course_offering", "venue", "time_slot", "semester"]]

    def __str__(self) -> str:
        return f"{self.course_offering} - {self.time_slot} @ {self.venue}"


class ExamTimetable(BaseModel):
    """Examination timetable entry."""
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="exam_timetable",
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
        related_name="exams",
    )
    exam_date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=120)
    invigilators = models.ManyToManyField(
        "users.User",
        related_name="exam_invigilation",
        blank=True,
    )
    state = FSMField(default="draft", choices=[
        ("draft", "Draft"),
        ("published", "Published"),
        ("completed", "Completed"),
    ])
    
    # For exam logistics
    total_students = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "timetable_exam"
        ordering = ["exam_date", "start_time"]

    def __str__(self) -> str:
        return f"{self.course_offering} - {self.exam_date}"

    @transition(field=state, source="draft", target="published")
    def publish(self):
        pass

    @transition(field=state, source="published", target="completed")
    def complete(self):
        pass


class TimetableConflict(BaseModel):
    """Detected timetable conflicts."""
    entry_type = models.CharField(max_length=20)  # "lecture" or "exam"
    entry_id = models.CharField(max_length=50)
    conflict_type = models.CharField(max_length=50)  # "venue", "lecturer", "time"
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)

    class Meta:
        db_table = "timetable_conflict"

    def __str__(self) -> str:
        return f"{self.conflict_type}: {self.description[:50]}"


# =====================================================
# Module 5.2 - ATTENDANCE MODELS
# =====================================================


class AttendanceSession(BaseModel):
    """Attendance session for a specific lecture/class."""
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    session_date = models.DateField()
    time_slot = models.ForeignKey(
        "timetable.TimeSlot",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    lecturer = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)
    total_registered = models.PositiveIntegerField(default=0)
    total_present = models.PositiveIntegerField(default=0)
    retention_until = models.DateField(null=True)

    class Meta:
        db_table = "attendance_session"
        unique_together = [["course_offering", "session_date"]]
        ordering = ["-session_date"]

    def __str__(self) -> str:
        return f"{self.course_offering} - {self.session_date}"

    def save(self, *args, **kwargs):
        from datetime import timedelta
        if not self.retention_until:
            self.retention_until = self.session_date + timedelta(days=365*5)
        super().save(*args, **kwargs)


class AttendanceRecord(BaseModel):
    """Individual student attendance record."""
    ATTENDANCE_STATUS = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("excused", "Excused"),
    ]

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="records",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
    )
    device_id = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "attendance_record"
        unique_together = [["session", "student"]]

    def __str__(self) -> str:
        return f"{self.student.matric_number}: {self.status}"


class AttendancePolicy(BaseModel):
    """Attendance policy per programme."""
    programme = models.ForeignKey(
        "institutional.Programme",
        on_delete=models.CASCADE,
        related_name="attendance_policies",
    )
    minimum_attendance_percent = models.PositiveSmallIntegerField(default=75)
    calculation_method = models.CharField(
        max_length=20,
        choices=[
            ("all_sessions", "All Sessions"),
            ("first_half", "First Half Only"),
            ("second_half", "Second Half Only"),
        ],
        default="all_sessions"
    )
    trigger_probation = models.BooleanField(default=True)
    trigger_debarment = models.BooleanField(default=True)

    class Meta:
        db_table = "attendance_policy"

    def __str__(self) -> str:
        return f"{self.programme}: {self.minimum_attendance_percent}%"


class StudentAttendanceSummary(BaseModel):
    """Aggregated attendance per student per course."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="attendance_summaries",
    )
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="student_summaries",
    )
    semester = models.ForeignKey(
        "institutional.Semester",
        on_delete=models.CASCADE,
        related_name="attendance_summaries",
    )
    total_sessions = models.PositiveIntegerField(default=0)
    present_count = models.PositiveIntegerField(default=0)
    absent_count = models.PositiveIntegerField(default=0)
    late_count = models.PositiveIntegerField(default=0)
    excused_count = models.PositiveIntegerField(default=0)
    attendance_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    meets_requirement = models.BooleanField(default=True)

    class Meta:
        db_table = "attendance_summary"
        unique_together = [["student", "course_offering", "semester"]]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.attendance_percent}%"
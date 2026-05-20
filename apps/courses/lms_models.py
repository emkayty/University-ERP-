"""
LMS Integration Models (Placeholder).
Module 5.3 - Learning Management System.
In production, integrate with: Moodle, Blackboard, Canvas.
"""

from django.db import models
from apps.core.models import BaseModel


class LMSCourse(BaseModel):
    """Course sync from external LMS."""
    local_course = models.OneToOneField(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="lms_course",
    )
    lms_course_id = models.CharField(max_length=50)
    lms_url = models.URLField()
    last_sync = models.DateTimeField(null=True)
    
    SYNC_STATUS = [
        ("synced", "Synced"),
        ("pending", "Pending"),
        ("error", "Error"),
    ]
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS, default="pending")

    class Meta:
        db_table = "lms_course"

    def __str__(self) -> str:
        return f"{self.local_course.code} -> {self.lms_course_id}"


class LMSEnrollment(BaseModel):
    """Student enrollment in LMS course."""
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="lms_enrollments",
    )
    lms_course = models.ForeignKey(
        LMSCourse,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    lms_user_id = models.CharField(max_length=50)
    last_activity = models.DateTimeField(null=True)
    progress_percent = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "lms_enrollment"
        unique_together = [["student", "lms_course"]]

    def __str__(self) -> str:
        return f"{self.student.matric_number} - {self.progress_percent}%"


class LMSGradeSync(BaseModel):
    """Grade sync with LMS."""
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="lms_grades",
    )
    lms_grade_url = models.URLField()
    last_sync = models.DateTimeField(null=True)

    class Meta:
        db_table = "lms_grade_sync"

    def __str__(self) -> str:
        return f"{self.course_offering} sync: {self.last_sync}"


class CourseMaterial(BaseModel):
    """Course materials/resources."""
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="materials",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=30)  # pdf, video, link, ppt
    url = models.URLField()
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "course_material"

    def __str__(self) -> str:
        return f"{self.course_offering}: {self.title}"
"""
Celery configuration for Nigerian University MIS.
Named queues for different task types.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("university_mis")

# Load configuration from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all apps
app.autodiscover_tasks()


# Named Celery queues configuration
app.conf.task_queues = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
    "payments": {
        "exchange": "payments",
        "routing_key": "payments",
    },
    "jamb": {
        "exchange": "jamb",
        "routing_key": "jamb",
    },
    "notifications": {
        "exchange": "notifications",
        "routing_key": "notifications",
    },
    "documents": {
        "exchange": "documents",
        "routing_key": "documents",
    },
    "ml": {
        "exchange": "ml",
        "routing_key": "ml",
    },
    "infra": {
        "exchange": "infra",
        "routing_key": "infra",
    },
}

# Celery Beat scheduled tasks
app.conf.beat_schedule = {
    # Database backup - daily at 1 AM
    "daily-db-backup": {
        "task": "apps.core.tasks.backup_database",
        "schedule": crontab(hour=1, minute=0),
        "options": {"queue": "infra"},
    },
    # Clean audit logs - monthly
    "clean-old-audit-logs": {
        "task": "apps.core.tasks.clean_audit_logs",
        "schedule": crontab(hour=2, minute=0, day_of_month=1),
        "options": {"queue": "infra"},
    },
    # Session sync - daily at midnight
    "sync-academic-session": {
        "task": "apps.academics.tasks.sync_academic_session",
        "schedule": crontab(hour=0, minute=0),
        "options": {"queue": "default"},
    },
    # JAMB sync - hourly during business hours
    "sync-jamb-data": {
        "task": "apps.admissions.tasks.sync_jamb",
        "schedule": crontab(minute=0),
        "options": {"queue": "jamb"},
    },
    # Payment reconciliation - every 15 minutes
    "reconcile-payments": {
        "task": "apps.finance.tasks.reconcile_payments",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "payments"},
    },
    # Notification batch - every 5 minutes
    "process-notifications": {
        "task": "apps.communication.tasks.process_notification_queue",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "notifications"},
    },
    # Document expiry check - daily at 6 AM
    "check-document-expiry": {
        "task": "apps.records.tasks.check_document_expiry",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "documents"},
    },
}

# Task routes - route tasks to specific queues
app.conf.task_routes = {
    "apps.finance.tasks.*": {"queue": "payments"},
    "apps.admissions.tasks.sync_jamb": {"queue": "jamb"},
    "apps.communication.tasks.*": {"queue": "notifications"},
    "apps.records.tasks.*": {"queue": "documents"},
    "apps.ml.tasks.*": {"queue": "ml"},
    "apps.core.tasks.backup_database": {"queue": "infra"},
    "apps.core.tasks.clean_audit_logs": {"queue": "infra"},
}

# Task serializations
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]

# Timezone
app.conf.timezone = "Africa/Lagos"
app.conf.enable_utc = True

# Result backend
app.conf.result_expires = 60 * 60 * 24 * 7  # 7 days

# Task tracking
app.conf.task_track_started = True
app.conf.task_send_sent_event = True

# Worker configuration
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 1000


@app.task(bind=True, default_retry_delay=60)
def debug_task(self) -> str:
    """Debug task to test Celery."""
    return f"Celery is working: {self.request.id}"
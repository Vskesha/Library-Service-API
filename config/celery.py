import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    from borrowings.tasks import check_overdue_borrowings_task

    sender.add_periodic_task(
        crontab(hour="5", minute="0"),
        check_overdue_borrowings_task.s(),
        name="Daily check of overdue borrowings",
    )
app.conf.beat_schedule = {
    "check-expired-stripe-sessions": {
        "task": "payments.tasks.check_expired_stripe_sessions",
        "schedule": 60.0,
    },
}
app.conf.timezone = "UTC"

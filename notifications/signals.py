from django.db.models.signals import post_save
from django.dispatch import receiver

from borrowings.models import Borrowing
# from notifications.tasks import send_new_notification


@receiver([post_save], sender=Borrowing)
def send_created_notification(sender, instance, created, **kwargs):
    if created:
        send_new_notification.delay_on_commit(instance.id)

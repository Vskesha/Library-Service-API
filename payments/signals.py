from django.db.models.signals import post_save
from django.dispatch import receiver

from payments.models import Payment
from payments.tasks import send_payment_notification_task


@receiver(post_save, sender=Payment)
def payment_completed(sender, instance, created, **kwargs):
    if not created and instance.status == Payment.Status.PAID:
        send_payment_notification_task.delay(instance.id)

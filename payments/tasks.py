from celery import shared_task

from payments.models import Payment
from payments.services.payment_notification_service import (
    PaymentNotificationService,
)


@shared_task
def send_payment_notification_task(payment_id: int):
    try:
        payment = Payment.objects.select_related(
            "borrowing__user", "borrowing__book"
        ).get(id=payment_id)
        if payment.status == Payment.Status.PAID:
            PaymentNotificationService().send_payment_notification(payment)
    except Payment.DoesNotExist:
        print(f"Payment with id={payment_id} not found")

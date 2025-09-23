from celery import shared_task
from payments.services.payment_notification_service import (
    PaymentNotificationService,
)
from django.utils import timezone
from .models import Payment
import stripe


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

@shared_task
def check_expired_stripe_sessions():
    pending_payments = Payment.objects.filter(status=Payment.Status.PENDING)

    for payment in pending_payments:
        try:
            session = stripe.checkout.Session.retrieve(payment.session_id)
            expires_at = session.expires_at
            current_time = int(timezone.now().timestamp())
            if expires_at <= current_time:
                payment.status = Payment.Status.EXPIRED
                payment.save()
        except stripe.error.InvalidRequestError:
            payment.status = Payment.Status.EXPIRED
            payment.save()

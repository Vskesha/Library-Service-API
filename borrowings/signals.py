import os
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver
from dotenv import load_dotenv

from borrowings.models import Borrowing
from notifications.tasks import send_borrowing_notification_task
from payments.models import Payment
from payments.services.create_stripe_session import StripePaymentService

load_dotenv()


@receiver(post_save, sender=Borrowing)
def create_payment(sender, instance, created, **kwargs):
    if created:
        rent_day = (instance.expected_return_date - instance.borrow_date).days
        book_price = instance.book.daily_fee
        total_count = rent_day * book_price

        data = {
            "product_data": {
                "name": f"Borrowing {instance.book.title} "
                f"({instance.book.author}) for {rent_day} day(s)"
            },
            "unit_amount": total_count,
        }
        payment_service = StripePaymentService()
        session = payment_service.create_payment_session(data)

        Payment.objects.create(
            borrowing=instance,
            money_to_pay=total_count,
            session_url=session.url,
            session_id=session.id,
        )


@receiver(post_save, sender=Borrowing)
def borrowing_created(sender, instance, created, **kwargs):
    if created:
        send_borrowing_notification_task.delay(instance.id)


@receiver(post_save, sender=Borrowing)
def create_fine_payment_on_overdue(sender, instance, created, **kwargs):
    """
    Creates a Fine Payment when book is returned after expected return date
    """

    if created or instance.actual_return_date is None:
        return

    fine_exists = Payment.objects.filter(
        borrowing=instance,
        type=Payment.Type.FINE,
    ).exists()

    if fine_exists:
        return

    overdue_days = (
        instance.actual_return_date - instance.expected_return_date
    ).days
    if overdue_days <= 0:
        return

    book = instance.book
    fine_amount = (
        Decimal(book.daily_fee)
        * Decimal(overdue_days)
        * Decimal(os.environ.get("FINE_MULTIPLIER", "1.00"))
    )

    data = {
        "product_data": {
            "name": f"Overdue borrowing {book.title} "
            f"({book.author} for {overdue_days} day(s)"
        },
        "unit_amount": fine_amount,
    }
    payment_service = StripePaymentService()
    session = payment_service.create_payment_session(data)

    Payment.objects.create(
        borrowing=instance,
        type=Payment.Type.FINE,
        money_to_pay=fine_amount,
        session_url=session.url,
        session_id=session.id,
    )

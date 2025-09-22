from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Borrowing
from payments.models import Payment
from payments.services.create_stripe_session import create_stripe_payment_session


@receiver(post_save, sender=Borrowing)
def create_payment_for_borrowing(sender, instance, created, **kwargs):
    if created:
        stripe_session = create_stripe_payment_session(instance)

        daily_rate = instance.book.daily_fee
        days = (instance.expected_return_date - instance.borrow_date).days
        amount = daily_rate * days

        Payment.objects.create(
            borrowing=instance,
            money_to_pay=amount,
            session_url=stripe_session.url,
            session_id=stripe_session.id,
            status="Pending"
        )

from django.db.models.signals import post_save
from django.dispatch import receiver

from payments.models import Payment
from payments.services.create_stripe_session import StripePaymentService
from .models import Borrowing


@receiver(post_save, sender=Borrowing)
def create_payment(sender, instance, created, **kwargs):
    if created:
        rent_day = (instance.expected_return_date - instance.borrow_date).days
        book_price = instance.book.daily_fee
        total_count = rent_day * book_price

        data = {
            "product_data": {"name": f"Borrowing #{instance.id}"},
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

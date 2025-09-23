import os
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.test import TestCase
from dotenv import load_dotenv

from books.models import Book
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

    if not created and instance.actual_return_date is not None:
        fine_exists = Payment.objects.filter(
            borrowing=instance,
            type=Payment.Type.FINE,
        ).exists()

        if fine_exists:
            return

        overdue_days = (
            instance.actual_return_date - instance.expected_return_date
        ).days
        if overdue_days > 0:
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


class BorrowingSignalsTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="123vs456",
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="H",
            inventory=10,
            daily_fee=Decimal("2.00"),
        )

        self.borrowing = Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=5),
            book=self.book,
            user=self.user,
        )

        self.mock_session = Mock()
        self.mock_session.url = "https://checkout.stripe.com/session123"
        self.mock_session.id = "session_123"

        self.mock_payment_service_instance = Mock()
        self.mock_payment_service_instance.create_payment_session.return_value = (
            self.mock_session
        )

    @patch("payments.services.create_stripe_session.StripePaymentService")
    def test_no_fine_on_return(self, mock_stripe_service):
        mock_stripe_service.return_value = self.mock_payment_service_instance

        self.borrowing.actual_return_date = date.today()
        self.borrowing.save()

        self.assertEqual(
            Payment.objects.filter(type=Payment.Type.FINE).count(), 0
        )

    @patch("payments.services.create_stripe_session.StripePaymentService")
    def test_fine_was_created_successfully(self, mock_stripe_service):
        mock_stripe_service.return_value = self.mock_payment_service_instance

        overdue_days = 5
        self.borrowing.actual_return_date = (
            self.borrowing.expected_return_date + timedelta(days=overdue_days)
        )
        self.borrowing.save()

        payments = Payment.objects.filter(
            borrowing=self.borrowing,
            type=Payment.Type.FINE,
        )
        self.assertEqual(len(payments), 1)

        payment = payments.first()
        expected_amount = (
            Decimal(self.book.daily_fee)
            * Decimal(overdue_days)
            * Decimal(os.environ.get("FINE_MULTIPLIER", "1.00"))
        )
        self.assertEqual(payment.money_to_pay, expected_amount)

import os
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment


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

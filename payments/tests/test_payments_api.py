from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch, MagicMock

from django.urls import reverse
from stripe import StripeError

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.services.create_stripe_session import StripePaymentService

PAYMENTS_URL = reverse("payments:payment-list")


def sample_user(**params):
    defaults = {
        "email": "user@example.com",
        "password": "testpass123",
        "first_name": "Iryna",
        "last_name": "Petrivna",
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


def payment_detail_url(payment_id):
    return reverse("payments:payment-detail", args=[payment_id])


def sample_book(**params):
    defaults = {
        "title": "Lord of the Rings",
        "author": "J. R. R. Tolkien",
        "cover": "H",
        "inventory": 100,
        "daily_fee": 0.10,
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


def sample_borrowing(**params):
    defaults = {
        "expected_return_date": date(2100, 12, 12),
        "book": sample_book(),
        "user": sample_user(),
    }

    return Borrowing.objects.create(**defaults)


def sample_payment(**params):
    defaults = {
        "status": "Paid",
        "type": "Payment",
        "borrowing": sample_borrowing(),
        "session_url": "pupupu.com",
        "session_id": "sess_123",
        "money_to_pay": 30.50,
    }
    defaults.update(params)

    return Payment.objects.create(**defaults)





class StripePaymentServiceTests(TestCase):
    def setUp(self):
        self.stripe_service = StripePaymentService()

    def test_create_payment_session(self):
        with patch("stripe.checkout.Session.create") as mock_create:
            mock_session = MagicMock()
            mock_session.id = "sess_123"
            mock_create.return_value = mock_session

            data = {"unit_amount": 10, "quantity": 2}
            session = self.stripe_service.create_payment_session(data)

            mock_create.assert_called_once()
            self.assertEqual(session.id, "sess_123")

    def test_mark_session_as_expired(self):
        with patch("stripe.checkout.Session.expire") as mock_expire:
            mock_session = MagicMock()
            mock_expire.return_value = mock_session

            result = self.stripe_service.mark_session_as_expired("sess_123")
            mock_expire.assert_called_once_with("sess_123")
            self.assertEqual(result, mock_session)

    def test_stripe_error_raised(self):
        with patch("stripe.checkout.Session.create",
                   side_effect=StripeError("Stripe is down")) as mock_create:
            mock_session = MagicMock()
            mock_session.id = "sess_123"
            mock_create.return_value = mock_session
            data = {"unit_amount": 10, "quantity": 2}
            with self.assertRaises(Exception) as context:
                self.stripe_service.create_payment_session(data)

            self.assertIn("Error creating stripe session: Stripe is down",
                          str(context.exception))

    def test_is_paid_true(self):
        with patch("stripe.checkout.Session.retrieve") as mock_retrieve:
            mock_session = MagicMock()
            mock_session.payment_status = "paid"
            mock_retrieve.return_value = mock_session

            result = self.stripe_service.is_paid("sess_123")
            self.assertTrue(result)

    def test_is_paid_stripe_error_exception(self):
        with patch("stripe.checkout.Session.retrieve",
                   side_effect=StripeError("Stripe is down")):
            result = self.stripe_service.is_paid("sess_123")
            self.assertFalse(result)

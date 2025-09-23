from datetime import date
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from stripe import StripeError

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.services.create_stripe_session import StripePaymentService
from payments.tests.tests_classes import NoMessagesTestCase

PAYMENTS_URL = reverse("payments:payment-list")


def payment_detail_url(payment_id):
    return reverse("payments:payment-detail", args=[payment_id])


def sample_user(**params):
    defaults = {
        "password": "testpass123",
        "first_name": "Iryna",
        "last_name": "Petrivna",
    }
    defaults.update(params)
    if "email" not in defaults:
        defaults["email"] = "user@example.com"

    return get_user_model().objects.create(**defaults)


def sample_book(**params):
    defaults = {
        "title": "Lord of the Rings",
        "author": "J. R. R. Tolkien",
        "cover": "Hard",
        "inventory": 100,
        "daily_fee": 0.10,
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


def sample_borrowing(**params):
    defaults = {
        "expected_return_date": date(2100, 12, 12),
    }
    defaults.update(params)
    if "user" not in defaults:
        defaults["user"] = sample_user()
    if "book" not in defaults:
        defaults["book"] = sample_book()

    return Borrowing.objects.create(**defaults)


def sample_payment(**params):
    defaults = {
        "status": "P",
        "type": "P",
        "session_url": "https://stripe.com/session",
        "session_id": "sess_123",
        "money_to_pay": 30.50,
    }
    defaults.update(params)
    if "borrowing" not in defaults:
        defaults["borrowing"] = sample_borrowing()

    return Payment.objects.create(**defaults)


class AuthenticatedPaymentApiTest(NoMessagesTestCase):
    """
    Tests payment API access for authenticated non-staff users.

    - Verifies that users can list and retrieve only their own payments.
    - Uses sample helpers to seed user, book, borrowing, and payment data.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)
        self.book = sample_book(title="Lord of the Rings 1")
        self.borrowing = sample_borrowing(book=self.book, user=self.user)
        self.payment = Payment.objects.get(borrowing=self.borrowing)

    def test_list_payments_for_user_only(self):
        res = self.client.get(PAYMENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["borrowing"]["id"], self.borrowing.id)

    def test_retrieve_users_payment(self):
        url = payment_detail_url(self.payment.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], self.payment.id)


class StaffPaymentApiTest(NoMessagesTestCase):
    """
    Tests payment API access for staff users.

    - Verifies that admin users can list all payments across all borrowings.
    """

    def setUp(self):
        self.client = APIClient()
        self.staff_user = sample_user(
            email="admin@example.com", password="adminpass123", is_staff=True
        )
        self.client.force_authenticate(user=self.staff_user)
        self.book1 = sample_book(title="Lord of the Rings 2")
        self.book2 = sample_book(title="Lord of the Rings 3")
        self.borrowing1 = sample_borrowing(
            user=sample_user(email="user1@example.com"), book=self.book1
        )
        self.borrowing2 = sample_borrowing(
            user=sample_user(email="user2@example.com"), book=self.book2
        )

    def test_staff_sees_all_payments(self):
        res = self.client.get(PAYMENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)


class UnauthenticatedPaymentApiTest(NoMessagesTestCase):
    """
    Tests payment API access for staff users.

    - Verifies that unauthenticated users cannot access list nor details views.
    """

    def setUp(self):
        self.client = APIClient()
        self.payment = sample_payment()

    def test_auth_required_for_payment_list(self):
        res = self.client.get(PAYMENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_for_payment_detail(self):
        url = payment_detail_url(self.payment.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class StripePaymentServiceTests(NoMessagesTestCase):
    """
    Tests core StripePaymentService methods.

    - Verifies session creation, expiration, and payment status handling.
    """

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
        with patch(
            "stripe.checkout.Session.create",
            side_effect=StripeError("Stripe is down"),
        ) as mock_create:
            mock_session = MagicMock()
            mock_session.id = "sess_123"
            mock_create.return_value = mock_session
            data = {"unit_amount": 10, "quantity": 2}
            with self.assertRaises(Exception) as context:
                self.stripe_service.create_payment_session(data)

            self.assertIn(
                "Error creating stripe session: Stripe is down",
                str(context.exception),
            )

    def test_is_paid_true(self):
        with patch("stripe.checkout.Session.retrieve") as mock_retrieve:
            mock_session = MagicMock()
            mock_session.payment_status = "paid"
            mock_retrieve.return_value = mock_session

            result = self.stripe_service.is_paid("sess_123")
            self.assertTrue(result)

    def test_is_paid_stripe_error_exception(self):
        with patch(
            "stripe.checkout.Session.retrieve",
            side_effect=StripeError("Stripe is down"),
        ):
            result = self.stripe_service.is_paid("sess_123")
            self.assertFalse(result)

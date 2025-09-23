import os
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.tests.tests_classes import NoMessagesTestCase

User = get_user_model()


class BorrowingViewSetTests(NoMessagesTestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.com", password="pass", is_staff=True
        )
        self.user1 = User.objects.create_user(
            email="user1@test.com", password="pass"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", password="pass"
        )

        self.book = Book.objects.create(
            title="Book1",
            author="Author1",
            cover="H",
            inventory=3,
            daily_fee=1,
        )

        self.borrowing1 = Borrowing.objects.create(
            user=self.user1,
            book=self.book,
            expected_return_date=timezone.now().date(),
        )
        self.borrowing2 = Borrowing.objects.create(
            user=self.user2,
            book=self.book,
            expected_return_date=timezone.now().date(),
        )

        self.client = APIClient()

    def test_create_borrowing_success(self):
        user = User.objects.create_user(
            email="user@test.com",
            password="pass123",
        )
        self.client.force_authenticate(user=user)

        self.client.post(
            reverse("borrowings:borrowing-list"),
            {
                "book": self.book.id,
                "expected_return_date": "2025-10-15",
            },
        )

        self.assertTrue(Borrowing.objects.filter(user=user).exists())

    def test_borrowing_creation_fails_when_payment_fails(self):
        with patch.object(
            Payment.objects,
            "create",
            side_effect=Exception("Cannot create payment"),
        ):

            user = User.objects.create_user(
                email="user@test.com",
                password="pass123",
            )
            self.client.force_authenticate(user=user)

            try:
                self.client.post(
                    reverse("borrowings:borrowing-list"),
                    {
                        "book": self.book.id,
                        "expected_return_date": "2025-10-15",
                    },
                )
            except Exception as e:
                print(e)
                pass

            self.assertFalse(Borrowing.objects.filter(user=user).exists())

    def test_user_sees_only_their_borrowings(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/borrowings/")
        self.assertEqual(response.status_code, 200)
        expected_count = Borrowing.objects.filter(user=self.user1).count()
        self.assertEqual(len(response.data), expected_count)

    def test_admin_sees_all_borrowings(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/borrowings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filter_is_active_true(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/borrowings/?is_active=true")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            all(b["actual_return_date"] is None for b in response.data)
        )

    def test_filter_is_active_false(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/borrowings/?is_active=false")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            all(b["actual_return_date"] is not None for b in response.data)
        )

    def test_filter_by_user_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/borrowings/?user_id={self.user1.id}")
        self.assertEqual(response.status_code, 200)

        returned_ids = {b["id"] for b in response.data}
        expected_ids = set(
            Borrowing.objects.filter(user=self.user1).values_list(
                "id", flat=True
            )
        )
        self.assertEqual(returned_ids, expected_ids)

    def test_user_can_return_own_borrowing(self):
        """Tests for return Borrowing"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(
            f"/api/borrowings/{self.borrowing1.id}/return/"
        )
        self.assertEqual(response.status_code, 200)

        self.borrowing1.refresh_from_db()
        self.book.refresh_from_db()

        self.assertIsNotNone(self.borrowing1.actual_return_date)
        today = timezone.now().date()
        self.assertEqual(self.borrowing1.actual_return_date, today)
        self.assertEqual(self.book.inventory, 4)

    def test_admin_can_return_any_borrowing(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/borrowings/{self.borrowing2.id}/return/"
        )
        self.assertEqual(response.status_code, 200)

        self.borrowing2.refresh_from_db()
        self.book.refresh_from_db()

        self.assertIsNotNone(self.borrowing2.actual_return_date)
        self.assertEqual(self.book.inventory, 4)

    def test_user_cannot_return_someone_else_borrowing(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            f"/api/borrowings/{self.borrowing1.id}/return/"
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.data)

    def test_cannot_return_borrowing_twice(self):
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            f"/api/borrowings/{self.borrowing1.id}/return/"
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            f"/api/borrowings/{self.borrowing1.id}/return/"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)


class BorrowingSignalsTest(NoMessagesTestCase):
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

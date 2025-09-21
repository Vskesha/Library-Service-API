from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book

BOOKS_URL = reverse("books:book-list")

def book_detail_url(book_id):
    return reverse("books:book-detail", args=[book_id])

def sample_book(**params):
    defaults = {
        "title": "Lord of the Rings",
        "author": "J. R. R. Tolkien",
        "cover": "H",
        "inventory": 100,
        "daily_fee": 0.10
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


class AdminApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            first_name="Lilichka",
            last_name="Cool",
            email="aboba@mail.com",
            password='adminpass123',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.book = sample_book()

    def test_get_books_admin(self):
        res = self.client.get(BOOKS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_put_book_admin(self):
        res = self.client.put(
            BOOKS_URL,
            data={
                "title": "he Hobbit, or There and Back Again",
                "author": "J. R. R. Tolkien",
                "cover": "H",
                "inventory": 100,
                "daily_fee": 0.10
            }
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_unique_book_constraint(self):
        sample_book()
        res = self.client.put(
            BOOKS_URL,
            data={
                "title": "Lord of the Rings",
                "author": "J. R. R. Tolkien",
                "cover": "S",
                "inventory": 50,
                "daily_fee": 0.20
            }
        )
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)


    def test_delete_book_allowed(self):
        book = sample_book()
        url = book_detail_url(book.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_put_show_session_admin(self):
        book = sample_book()
        url = book_detail_url(book.id)
        payload = {
            "title": "The Hobbit, or There and Back Again",
            "author": "J. R. R. Tolkien",
            "cover": "H",
            "inventory": 100,
            "daily_fee": 0.10
        }
        res = self.client.put(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]["title"],
                         "The Hobbit, or There and Back Again")


class UnauthenticatedApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.book = sample_book()

    def test_auth_required_for_book_details(self):
        res = self.client.get(book_detail_url(self.book.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_for_book_create(self):
        payload = {
            "title": "The Hobbit, or There and Back Again",
            "author": "J. R. R. Tolkien",
            "cover": "H",
            "inventory": 100,
            "daily_fee": 0.10
        }
        res = self.client.post(BOOKS_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorised_user_can_access_list(self):
        res = self.client.get(BOOKS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserModelTests(APITestCase):

    def test_create_user_with_email_successful(self):
        email = "test@example.com"
        password = "testpass123"
        user = User.objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_with_additional_fields(self):
        email = "test@example.com"
        password = "testpass123"
        first_name = "Test"
        last_name = "User"

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        self.assertEqual(user.email, email)
        self.assertEqual(user.first_name, first_name)
        self.assertEqual(user.last_name, last_name)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        sample_emails = [
            ["test@EXAMPLE.com", "test@example.com"],
            ["Test@Example.com", "Test@example.com"],
            ["TEST@EXAMPLE.COM", "TEST@example.com"],
            ["test1@example.COM", "test1@example.com"],
        ]
        for email, expected in sample_emails:
            user = User.objects.create_user(email, "sample123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("", "test123")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            "test@example.com",
            "test123",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_superuser_with_is_staff_false_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="test@example.com",
                password="test123",
                is_staff=False,
            )

    def test_create_superuser_with_is_superuser_false_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="test@example.com",
                password="test123",
                is_superuser=False,
            )

    def test_full_name_property(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="test123",
            first_name="John",
            last_name="Doe",
        )

        self.assertEqual(user.full_name, "John Doe")

    def test_full_name_property_empty_names(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="test123",
        )

        self.assertEqual(user.full_name, "")


class UserSerializerTests(APITestCase):

    def setUp(self):
        from users.serializers import UserSerializer

        self.serializer_class = UserSerializer

    def test_create_user_serializer_valid_data(self):
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        serializer = self.serializer_class(data=payload)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.email, payload["email"])
        self.assertEqual(user.first_name, payload["first_name"])
        self.assertEqual(user.last_name, payload["last_name"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", serializer.data)

    def test_password_too_short(self):
        payload = {
            "email": "test@example.com",
            "password": "123",
        }

        serializer = self.serializer_class(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_password_is_write_only(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )

        serializer = self.serializer_class(user)
        self.assertNotIn("password", serializer.data)

    def test_update_user_password(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )

        payload = {"password": "newpassword123"}
        serializer = self.serializer_class(user, data=payload, partial=True)

        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertTrue(updated_user.check_password("newpassword123"))
        self.assertFalse(updated_user.check_password("testpass123"))

    def test_update_user_email(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )

        payload = {"email": "newemail@example.com"}
        serializer = self.serializer_class(user, data=payload, partial=True)

        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertEqual(updated_user.email, "newemail@example.com")


class CreateUserAPITests(APITestCase):

    def setUp(self):
        self.create_url = reverse("user:create")

    def test_create_user_success(self):
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        res = self.client.post(self.create_url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_exists(self):
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
        }
        User.objects.create_user(**payload)

        res = self.client.post(self.create_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {
            "email": "test@example.com",
            "password": "pw",
        }

        res = self.client.post(self.create_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = User.objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test_create_user_invalid_email(self):
        payload = {
            "email": "invalid-email",
            "password": "testpass123",
        }

        res = self.client.post(self.create_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_missing_email(self):
        payload = {
            "password": "testpass123",
            "first_name": "Test",
        }

        res = self.client.post(self.create_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_missing_password(self):
        payload = {
            "email": "test@example.com",
            "first_name": "Test",
        }

        res = self.client.post(self.create_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ManageUserAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.manage_url = reverse("user:manage")

    def test_retrieve_profile_success(self):
        self.client.force_authenticate(user=self.user)

        res = self.client.get(self.manage_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "id": self.user.id,
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "is_staff": self.user.is_staff,
            },
        )

    def test_post_me_not_allowed(self):
        self.client.force_authenticate(user=self.user)

        res = self.client.post(self.manage_url, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }

        res = self.client.patch(self.manage_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, payload["first_name"])
        self.assertEqual(self.user.last_name, payload["last_name"])
        self.assertEqual(self.user.email, payload["email"])

    def test_update_user_password(self):
        self.client.force_authenticate(user=self.user)

        payload = {"password": "newpassword123"}

        res = self.client.patch(self.manage_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["password"]))

    def test_retrieve_user_unauthorized(self):
        res = self.client.get(self.manage_url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.token_url = reverse("user:token_obtain_pair")
        self.refresh_url = reverse("user:token_refresh")
        self.verify_url = reverse("user:token_verify")

    def test_obtain_token_success(self):
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
        }

        res = self.client.post(self.token_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_obtain_token_invalid_credentials(self):
        payload = {
            "email": "test@example.com",
            "password": "wrongpassword",
        }

        res = self.client.post(self.token_url, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", res.data)

    def test_obtain_token_missing_email(self):
        payload = {"password": "testpass123"}

        res = self.client.post(self.token_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtain_token_missing_password(self):
        payload = {"email": "test@example.com"}

        res = self.client.post(self.token_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_success(self):
        refresh = RefreshToken.for_user(self.user)
        payload = {"refresh": str(refresh)}

        res = self.client.post(self.refresh_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_refresh_token_invalid(self):
        payload = {"refresh": "invalid-token"}

        res = self.client.post(self.refresh_url, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_token_success(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        payload = {"token": access_token}

        res = self.client.post(self.verify_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_verify_token_invalid(self):
        payload = {"token": "invalid-token"}

        res = self.client.post(self.verify_url, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class UserManagerTests(APITestCase):

    def test_create_user_manager_method(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser_manager_method(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )

        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.check_password("adminpass123"))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_manager_use_in_migrations(self):
        self.assertTrue(User.objects.use_in_migrations)


class URLTests(APITestCase):

    def test_create_user_url_resolves(self):
        url = reverse("user:create")
        self.assertTrue(url.endswith("/register/"))

    def test_manage_user_url_resolves(self):
        url = reverse("user:manage")
        self.assertTrue(url.endswith("/me/"))

    def test_token_obtain_pair_url_resolves(self):
        url = reverse("user:token_obtain_pair")
        self.assertTrue(url.endswith("/token/"))

    def test_token_refresh_url_resolves(self):
        url = reverse("user:token_refresh")
        self.assertTrue(url.endswith("/token/refresh/"))

    def test_token_verify_url_resolves(self):
        url = reverse("user:token_verify")
        self.assertTrue(url.endswith("/token/verify/"))

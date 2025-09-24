from unittest.mock import patch

from django.db.models.signals import post_save
from django.test import override_settings
from rest_framework.test import APITestCase

from borrowings.models import Borrowing
from borrowings.signals import borrowing_created


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_BROKER_URL="memory://",
)
class NoMessagesTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(borrowing_created, sender=Borrowing)

    def setUp(self):
        super().setUp()
        patch(
            "borrowings.tasks.send_borrowing_notification_task.apply_async",
            autospec=True,
        ).start()
        patch(
            "borrowings.tasks.send_borrowing_notification_task.delay",
            autospec=True,
        ).start()

        patch("telegram.Bot.send_message", autospec=True).start()

    def tearDown(self):
        patch.stopall()
        super().tearDown()

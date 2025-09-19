from django.conf import settings

from borrowings.services.telegram_bot_service import BaseTelegramBotService
from borrowings.models import Borrowing


class NotificationTelegramBotService(BaseTelegramBotService):
    def __init__(self, token=settings.MESSAGE_TELEGRAM_BOT_TOKEN):
        super().__init__(token)

    @staticmethod
    def _get_notification_created_text(borrowing: Borrowing) -> str:
        return f"New borrowing created: {borrowing.text_preview}\nuser: {borrowing.user.username}"

    def send_notification_created(self, borrowing: Borrowing):
        text = self._get_notification_created_text(borrowing)

        if borrowing.user.telegram_id:
            self.send_notification(borrowing.user.telegram_id, text)

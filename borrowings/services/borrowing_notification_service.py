from django.conf import settings

from borrowings.models import Borrowing
from notifications.services.telegram_bot_service import TelegramBotService


class BorrowingNotificationService(TelegramBotService):
    def __init__(self):
        super().__init__(settings.TELEGRAM_BOT_TOKEN)

    @staticmethod
    def _format_borrowing_notification(borrowing: Borrowing) -> str:
        return (
            f" New Borrowing Created\n"
            f"User: {borrowing.user.full_name}\n"
            f"Book: {borrowing.book.title} by {borrowing.book.author}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Expected return: {borrowing.expected_return_date}\n"
            f"Actual return: {borrowing.actual_return_date or '—'}"
        )

    def send_borrowing_notification(self, borrowing: Borrowing) -> None:
        text = self._format_borrowing_notification(borrowing)
        self.send_notification(settings.TELEGRAM_ADMIN_CHAT_ID, text=text)

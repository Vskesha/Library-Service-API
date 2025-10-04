from django.conf import settings
from django.utils import timezone

from borrowings.models import Borrowing
from notifications.services.telegram_bot_service import TelegramBotService


class BorrowingNotificationService(TelegramBotService):
    def __init__(self):
        super().__init__(settings.TELEGRAM_BOT_TOKEN)

    @staticmethod
    def _format_borrowing_notification(borrowing: Borrowing) -> str:
        return (
            f"New Borrowing Created\n"
            f"👤 User: {borrowing.user.full_name}\n"
            f"📚 Book: {borrowing.book.title} by {borrowing.book.author}\n"
            f"📅 Borrow date: {borrowing.borrow_date}\n"
            f"📅 Expected return: {borrowing.expected_return_date}\n"
            f"📅 Actual return: {borrowing.actual_return_date or '—'}"
        )

    def send_borrowing_notification(self, borrowing: Borrowing) -> None:
        text = self._format_borrowing_notification(borrowing)
        self.send_notification(settings.TELEGRAM_ADMIN_CHAT_ID, text=text)

    def check_overdue_borrowings(self) -> None:
        overdue_borrowings = Borrowing.objects.filter(
            actual_return_date=None,
            expected_return_date__lt=timezone.localdate(),
        ).select_related("book", "user")

        if overdue_borrowings.exists():
            borrowings_by_user = {}

            for borrowing in overdue_borrowings:
                borrowings_by_user.setdefault(
                    borrowing.user.full_name, []
                ).append(borrowing)

            text_parts = []
            for user, borrowings in borrowings_by_user.items():
                count_borrowings = len(borrowings)
                user_text = (
                    f"{user} has {count_borrowings} "
                    f"borrowing{'s' if count_borrowings > 1 else ''}:\n"
                )
                borrowings_text = "\n".join(
                    f"📕 {borrowing.book.title} "
                    f"(Return date: {borrowing.expected_return_date})"
                    for borrowing in borrowings
                )
                text_parts.append(user_text + borrowings_text)

            text = "Borrowings Info 📚\n\n" + "\n\n".join(text_parts)
        else:
            text = "No borrowings overdue today! ✅"

        self.send_notification(settings.TELEGRAM_ADMIN_CHAT_ID, text=text)

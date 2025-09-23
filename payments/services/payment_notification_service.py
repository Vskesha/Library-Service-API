from django.conf import settings

from notifications.services.telegram_bot_service import TelegramBotService
from payments.models import Payment


class PaymentNotificationService(TelegramBotService):
    def __init__(self):
        super().__init__(settings.TELEGRAM_BOT_TOKEN)

    @staticmethod
    def _format_payment_notification(payment: Payment) -> str:
        return (
            f"💳 <b>Payment Successful</b>\n\n"
            f"👤 User: {payment.borrowing.user.username}\n"
            f"📚 Book: {payment.borrowing.book.title}\n"
            f"💰 Amount: {payment.money_to_pay} UAH\n"
            f"📂 Type: {payment.type}\n"
            f"📅 Status: {payment.status}\n"
            f"🔗 <a href='{payment.session_url}'>Payment Session</a>"
        )

    def send_payment_notification(self, payment: Payment) -> None:
        text = self._format_payment_notification(payment)
        self.send_notification(settings.TELEGRAM_ADMIN_CHAT_ID, text=text)

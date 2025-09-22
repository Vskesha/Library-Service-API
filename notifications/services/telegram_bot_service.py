import telebot
from django.conf import settings

from notifications.services.bot_service import BaseBotService


class TelegramBotService(BaseBotService):
    def __init__(self, token: str = settings.TELEGRAM_BOT_TOKEN):
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is missing in settings")
        self._bot = telebot.TeleBot(token, parse_mode="HTML")

    def send_notification(
        self, chat_id: int | str, text: str, **kwargs
    ) -> None:
        try:
            self._bot.send_message(chat_id, text, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Telegram API error: {e}")

import requests
from django.conf import settings
from .bot_service import BaseBotService

class TelegramBotService:
    def __init__(self, token: str = settings.TELEGRAM_BOT_TOKEN):
        self.base_url = f"https://api.telegram.org/bot{token}/"

    def send_notification(self, chat_id: int | str, text: str, **kwargs) -> None:
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": kwargs.get("parse_mode", "HTML"),
        }
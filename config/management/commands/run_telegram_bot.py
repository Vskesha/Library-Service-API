import telebot
from django.conf import settings
from django.core.management.base import BaseCommand

from borrowings.tasks import check_overdue_borrowings_task
from notifications.services.telegram_bot_service import TelegramBotService


class Command(BaseCommand):
    help = "Runs telegram bot"

    def handle(self, *args, **options):
        self.stdout.write("Running telegram bot")

        bot_service = TelegramBotService()
        bot = bot_service._bot

        bot.set_my_commands(
            [
                telebot.types.BotCommand("/start", "Start bot"),
                telebot.types.BotCommand("/debtors", "Return list of debtors"),
            ]
        )

        @bot.message_handler(commands=["start"])
        def start_handler(message):
            bot_service.send_notification(
                settings.TELEGRAM_ADMIN_CHAT_ID,
                "Library Telegram Bot started 🚀",
            )

        @bot.message_handler(commands=["debtors"])
        def list_debtors(message):
            check_overdue_borrowings_task.delay()

        bot.infinity_polling()

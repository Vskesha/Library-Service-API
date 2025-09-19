# from celery import shared_task

# from notifications.models import Notification
# from notifications.services.telegram_bot_service import (
#     NotificationTelegramBotService,
# )
#

# @shared_task
# def send_new_notification(notification_id):
#     notification = Notification.objects.get(id=notification_id)
#
#     service = NotificationTelegramBotService()
#     service.send_notification_created(notification)

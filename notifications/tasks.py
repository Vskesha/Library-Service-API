from celery import shared_task

from borrowings.models import Borrowing
from borrowings.services.borrowing_notification_service import (
    BorrowingNotificationService,
)


@shared_task
def send_borrowing_notification_task(borrowing_id: int):
    try:
        borrowing = Borrowing.objects.select_related("user", "book").get(
            id=borrowing_id
        )
        BorrowingNotificationService().send_borrowing_notification(borrowing)
    except Borrowing.DoesNotExist:
        print(f"Borrowing with id={borrowing_id} not found")

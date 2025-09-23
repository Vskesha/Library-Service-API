from config.celery import app


@app.task
def check_overdue_borrowings_task():
    from borrowings.services.borrowing_notification_service import (
        BorrowingNotificationService,
    )

    BorrowingNotificationService().check_overdue_borrowings()

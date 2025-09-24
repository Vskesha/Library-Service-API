from django.db import models

from borrowings.models import Borrowing


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        PAID = "Paid", "Paid"
        CANCELLED = "Cancelled", "Cancelled"
        EXPIRED = "Expired", "Expired"

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    class Type(models.TextChoices):
        PAYMENT = ("Payment", "Payment")
        FINE = ("Fine", "Fine")

    type = models.CharField(
        max_length=10,
        choices=Type.choices,
        default=Type.PAYMENT,
    )
    borrowing = models.ForeignKey(
        Borrowing,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    session_url = models.URLField(max_length=1000)
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ("-id",)

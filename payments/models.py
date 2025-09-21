from django.db import models

from borrowings.models import Borrowing


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PND", "Pending"
        PAID = "P", "Paid"

    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.PENDING,
    )

    class Type(models.TextChoices):
        PAYMENT = ("P", "Payment")
        FINE = ("F", "Fine")

    type = models.CharField(
        max_length=1,
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

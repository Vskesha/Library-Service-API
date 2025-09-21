from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.constraints import UniqueConstraint


class Book(models.Model):
    class Cover(models.TextChoices):
        HARD = (
            "H",
            "Hard",
        )
        SOFT = (
            "S",
            "Soft",
        )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(
        max_length=1,
        choices=Cover.choices,
        default=Cover.SOFT,
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        UniqueConstraint(fields=["title", "author"], name="unique_book")

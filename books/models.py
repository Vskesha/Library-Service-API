from django.contrib.auth import get_user_model
from django.db import models


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
    author = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="books"
    )
    cover = models.CharField(
        max_length=1,
        choices=Cover.choices,
        default=Cover.SOFT,
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

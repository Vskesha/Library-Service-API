from django.db import models
from django.db.models.constraints import UniqueConstraint


class Book(models.Model):
    class Cover(models.TextChoices):
        HARD = ("Hard", "Hard")
        SOFT = ("Soft", "Soft")

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(
        max_length=5,
        choices=Cover.choices,
        default=Cover.SOFT,
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["title", "author"],
                name="unique_book",
            )
        ]
        ordering = ("title",)

    def __str__(self):
        return f"{self.title} - {self.author} ({self.inventory} available)"

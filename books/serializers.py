from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")

    def validate_inventory(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Inventory must be zero or positive.")
        return value
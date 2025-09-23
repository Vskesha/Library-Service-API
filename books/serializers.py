from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    """
    Serializes Book model fields for API representation.

    - Includes all fields required for CRUD operations.
    - Used by BookViewset for all endpoints
    """

    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")

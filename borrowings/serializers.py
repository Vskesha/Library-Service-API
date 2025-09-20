from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing
from users.serializers import UserSerializer


class BorrowingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        )
        read_only_fields = ("id", "borrow_date", "actual_return_date")


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="title",
    )
    user = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="full_name",
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )
        read_only_fields = (
            "id",
            "borrow_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingDetailSerializer(BorrowingListSerializer):
    book = BookSerializer()
    user = UserSerializer()

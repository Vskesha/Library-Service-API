from rest_framework import serializers

from borrowings.serializers import BorrowingListSerializer
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = BorrowingListSerializer(
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
        )


class PaymentListSerializer(serializers.ModelSerializer):
    borrowing = serializers.SlugRelatedField(read_only=True, slug_field="id")

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "money_to_pay",
        )


class PaymentDetailSerializer(PaymentSerializer):
    """
    Extends PaymentSerializer for detailed views.

    Inherits from PaymentSerializer and currently shares the same fields.
    Defined separately to support future enhancements
    """

    pass

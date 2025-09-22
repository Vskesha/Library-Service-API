from rest_framework import serializers

from borrowings.serializers import BorrowingSerializer
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = serializers.SlugRelatedField(read_only=True, slug_field="id")

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
    borrowing = BorrowingSerializer(
        read_only=True,
    )

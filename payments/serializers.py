from rest_framework import serializers

from borrowings.serializers import BorrowingListSerializer, BorrowingSerializer
from payments.models import Payment
from payments.services.create_stripe_session import StripePaymentService


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
    borrowing = BorrowingSerializer(
        read_only=True,
    )


class PaymentRenewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "session_url",
            "session_id",
        )

    def validate(self, data):
        payment = self.instance
        if payment.status != Payment.Status.EXPIRED:
            raise serializers.ValidationError(
                "Only EXPIRED payments can be renewed."
            )
        return data

    def update(self, instance, validated_data):
        payment_service = StripePaymentService()
        borrowing = instance.borrowing
        data = {
            "product_data": {"name": f"Book: {borrowing.book.title}"},
            "unit_amount": float(instance.money_to_pay),
            "quantity": 1,
        }
        session = payment_service.create_payment_session(data)
        instance.session_url = session.url
        instance.session_id = session.id
        instance.status = Payment.Status.PENDING
        instance.save()
        return instance

from rest_framework import serializers

from borrowings.serializers import BorrowingListSerializer, BorrowingSerializer
from payments.models import Payment
from payments.services.create_stripe_session import StripePaymentService


class PaymentSerializer(serializers.ModelSerializer):
    """
    BaseSerializer.

    - Used by PaymentDetailSerializer.
    - Contains all fields from the Payment model.
    - For "borrowing" fields the BorrowingListSerializer is used to provide
    full borrowing details.
    """

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
    """
    List serializer.

    - Contains "id", "status", "type", "borrowing" and "money_to_pay",
    fields from the Payment model.
    - For "borrowing" fields the SlugRelatedField is used to
    show only the borrowing ID.
    """

    borrowing = BorrowingSerializer(read_only=True)
    user = serializers.CharField(
        read_only=True, source="borrowing.user.full_name"
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
            "user",
        )


class PaymentDetailSerializer(PaymentSerializer):
    """
    Extends PaymentSerializer for detailed views.

    - Inherits from PaymentSerializer and currently shares the same fields.
    - Defined separately to support future enhancements.
    """

    pass
    borrowing = BorrowingSerializer(
        read_only=True,
    )
    user = serializers.CharField(
        read_only=True, source="borrowing.user.full_name"
    )

    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + ("user",)


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

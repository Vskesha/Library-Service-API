from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.serializers import (
    PaymentDetailSerializer,
    PaymentListSerializer,
    PaymentSerializer,
)
from payments.services.create_stripe_session import StripePaymentService


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Payment.objects.select_related("borrowing")

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        if self.action == "retrieve":
            return PaymentDetailSerializer
        return PaymentSerializer

    def get_queryset(self):
        queryset = Payment.objects.select_related("borrowing")
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(borrowing__user=user)
        return queryset

    @action(detail=False, methods=["get"], url_path="success")
    def success(self, request: Request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"error": "Missing session_id in query params."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = get_object_or_404(Payment, session_id=session_id)

        if payment.status == Payment.Status.PAID:
            return Response(
                {"error": "This payment has already been marked as paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if payment.status == Payment.Status.CANCELLED:
            return Response(
                {"error": "This payment was previously cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe_service = StripePaymentService()
        if stripe_service.is_paid(session_id):
            payment.status = Payment.Status.PAID
            payment.save(update_fields=["status"])
            return Response({"message": "Your payment was processed successfully."})

        return Response({"message": "Payment is not confirmed yet."})

    @action(detail=False, methods=["get"], url_path="cancel")
    def cancel(self, request: Request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"error": "Missing session_id in query params."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = get_object_or_404(Payment, session_id=session_id)

        if payment.status in (Payment.Status.CANCELLED, Payment.Status.PAID):
            return Response(
                {"error": f"Payment is already {payment.status.lower()}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            payment.status = Payment.Status.CANCELLED
            payment.save(update_fields=["status"])

            Borrowing.objects.filter(id=payment.borrowing_id).update(
                actual_return_date=timezone.now()
            )

            StripePaymentService().mark_session_as_expired(session_id)

            Book.objects.filter(id=payment.borrowing.book_id).update(
                inventory=F("inventory") + 1
            )

        return Response(
            {"message": "Payment was cancelled. You can retry within 24 hours."}
        )

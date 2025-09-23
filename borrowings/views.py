from django.db import transaction
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.filters import BorrowingFilter
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingCreateSerializer,
    BorrowingDetailSerializer,
    BorrowingListSerializer,
    BorrowingSerializer,
)
from payments.models import Payment


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.all().select_related()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = BorrowingFilter

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        if self.action == "create":
            return BorrowingCreateSerializer
        return BorrowingSerializer

    def perform_create(self, serializer):
        has_pending_payment = Payment.objects.filter(
            borrowing__user=self.request.user,
            status=Payment.Status.PENDING,
        ).exists()
        if has_pending_payment:
            raise PermissionDenied(
                "You have unpaid payments. "
                "Please settle them before borrowing new books."
            )
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_staff:
            queryset = queryset.filter(user=user)

        return queryset

    @action(
        methods=["POST"],
        detail=True,
        url_path="return",
    )
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            return Response(
                {"error": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.is_staff and borrowing.user != request.user:
            return Response(
                {"error": "You can return only your own borrowings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            borrowing.actual_return_date = now().date()
            borrowing.book.inventory += 1
            borrowing.book.save()
            borrowing.save()
        return Response(
            BorrowingDetailSerializer(borrowing).data,
            status=status.HTTP_200_OK,
        )

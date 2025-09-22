from django.shortcuts import render
from rest_framework import mixins, viewsets

from payments.models import Payment
from payments.serializers import (
    PaymentListSerializer,
    PaymentDetailSerializer,
    PaymentSerializer,
)


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
        if self.action == "list":
            if self.request.user.is_staff:
                queryset = Payment.objects.all()
            elif not self.request.user.is_staff:
                queryset = Payment.objects.filter(
                    borrowing__user__id=self.request.user.id
                )
        return queryset

from django.urls import include, path
from rest_framework import routers

from payments.views import PaymentViewSet, PaymentRenewView

router = routers.DefaultRouter()

router.register("payments", PaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("payments/<int:pk>/renew/", PaymentRenewView.as_view(), name="payment-renew"),
]

app_name = "payments"

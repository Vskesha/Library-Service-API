from django.urls import include, path
from rest_framework import routers

from payments.views import PaymentViewSet

router = routers.DefaultRouter()

router.register("payments", PaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "payments"

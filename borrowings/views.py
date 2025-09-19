from rest_framework import generics

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingReadSerializer


class BorrowingViewSet(generics.ListAPIView):
    queryset = Borrowing.objects.all().select_related()
    serializer_class = BorrowingReadSerializer

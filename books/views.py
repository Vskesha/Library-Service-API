from rest_framework import viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication

from books.models import Book
from books.permissions import IsAdminOrReadOnly
from books.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    queryset = Book.objects.all()
    authentication_classes = (JWTAuthentication, )
    permission_classes = (IsAdminOrReadOnly, )

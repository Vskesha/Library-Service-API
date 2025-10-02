from rest_framework import viewsets

from books.models import Book
from books.permissions import IsAdminOrReadOnly
from books.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD endpoints for the Book model.

    - Non-admin users can only perform GET (list/retrieve).
    - Admin users may POST, PUT/PATCH and DELETE.
    """

    serializer_class = BookSerializer
    queryset = Book.objects.all()
    permission_classes = (IsAdminOrReadOnly,)

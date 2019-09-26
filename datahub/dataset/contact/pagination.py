from rest_framework.pagination import CursorPagination


class ContactsDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for ContactsDatasetView
    """

    ordering = ('created_on', 'pk')

from rest_framework.pagination import CursorPagination


class OMISDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for OMISDatasetView
    """

    ordering = ('created_on', 'pk')


class ContactsDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for ContactsDatasetView
    """

    ordering = ('created_on', 'pk')


class InteractionsDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for InteractionsDatasetView
    """

    ordering = ('created_on', 'pk')

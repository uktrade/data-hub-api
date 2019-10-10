from rest_framework.pagination import CursorPagination


class InteractionsDatasetViewCursorPagination(CursorPagination):
    """Cursor Pagination for InteractionsDatasetView"""

    ordering = ('created_on', 'pk')

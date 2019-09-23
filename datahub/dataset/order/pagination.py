from rest_framework.pagination import CursorPagination


class OMISDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for OMISDatasetView
    """

    ordering = ('created_on', 'pk')

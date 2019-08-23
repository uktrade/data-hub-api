from rest_framework.pagination import CursorPagination


class OMISDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for OMISDatasetView
    """

    ordering = ('created_date', 'omis_order_reference')

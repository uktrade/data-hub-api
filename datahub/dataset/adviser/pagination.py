from rest_framework.pagination import CursorPagination


class AdvisersDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for AdvisersDatasetView
    """

    ordering = ('date_joined', 'pk')

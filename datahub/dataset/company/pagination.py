from rest_framework.pagination import CursorPagination


class CompaniesDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for CompaniesDatasetView
    """

    ordering = ('created_on', 'pk')

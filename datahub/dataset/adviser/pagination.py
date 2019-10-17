from datahub.dataset.core.pagination import DatasetCursorPagination


class AdvisersDatasetViewCursorPagination(DatasetCursorPagination):
    """
    Cursor Pagination for AdvisersDatasetView
    """

    ordering = ('date_joined', 'pk')

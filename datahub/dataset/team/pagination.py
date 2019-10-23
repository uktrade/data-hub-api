from datahub.dataset.core.pagination import DatasetCursorPagination


class TeamsDatasetViewCursorPagination(DatasetCursorPagination):
    """
    Cursor Pagination for TeamsDatasetView
    """

    ordering = ('id',)

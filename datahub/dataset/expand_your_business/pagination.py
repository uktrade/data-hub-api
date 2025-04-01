from datahub.dataset.core.pagination import DatasetCursorPagination


class EYBDatasetViewCursorPagination(DatasetCursorPagination):
    """Cursor Pagination for AdvisersDatasetView."""

    ordering = ('modified_on', 'created_on')

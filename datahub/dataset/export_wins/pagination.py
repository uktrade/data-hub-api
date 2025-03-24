from datahub.dataset.core.pagination import DatasetCursorPagination


class HVCDatasetViewCursorPagination(DatasetCursorPagination):
    """Cursor Pagination for ExportWinsHVCDatasetView.
    """

    ordering = ('id',)

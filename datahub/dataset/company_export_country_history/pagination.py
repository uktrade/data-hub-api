from datahub.dataset.core.pagination import DatasetCursorPagination


class CompanyExportCountryHistoryDatasetViewCursorPagination(DatasetCursorPagination):
    """
    Cursor Pagination for CompanyExportCountryHistory
    """

    ordering = ('history_date', 'id')

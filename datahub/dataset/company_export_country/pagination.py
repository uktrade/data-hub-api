from datahub.dataset.core.pagination import DatasetCursorPagination


class CompanyExportCountryDatasetViewCursorPagination(DatasetCursorPagination):
    """
    Cursor Pagination for CompanyExportCountry
    """

    ordering = ('id',)

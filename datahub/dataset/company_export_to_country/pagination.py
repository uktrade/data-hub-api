from datahub.dataset.core.pagination import DatasetCursorPagination


class CompanyExportToCountriesDatasetViewCursorPagination(DatasetCursorPagination):
    """
    Cursor Pagination for CompanyExportToCountries
    """

    ordering = ('id', )

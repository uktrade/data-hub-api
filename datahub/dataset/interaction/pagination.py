from datahub.dataset.core.pagination import DatasetCursorPagination


class InteractionsExportCountryPagination(DatasetCursorPagination):
    """
    Cursor Pagination for CompanyFutureInterestCountries
    """

    ordering = ('created_on', 'id')

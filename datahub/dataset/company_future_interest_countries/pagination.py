from datahub.dataset.core.pagination import DatasetCursorPagination


class CompanyFutureInterestCountriesDatasetViewCursorPagination(DatasetCursorPagination):
    """
    Cursor Pagination for CompanyFutureInterestCountries
    """

    ordering = ('id', )

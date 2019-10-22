from rest_framework.pagination import CursorPagination


class CompanyFutureInterestCountriesDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for CompanyFutureInterestCountries
    """

    ordering = ('id', 'future_interest_countries__iso_alpha2_code')

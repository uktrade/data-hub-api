from rest_framework.pagination import CursorPagination


class CompanyFutureInterestCountriesDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for CompanyFutureInterestCountries
    """

    # ordering = ('company_id', 'country_id')
    ordering = ('id', 'future_interest_countries', )

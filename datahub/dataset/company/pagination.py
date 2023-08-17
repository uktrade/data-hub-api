from datahub.dataset.core.pagination import DatasetCursorPagination


class CompaniesDatasetViewCursorPagination(DatasetCursorPagination):
    """
    Cursor Pagination for CompaniesDatasetView
    """

    # Ordering by modified_on allows clients to fetch only what has changed
    # since they last ran. The only works robustly as long as data from
    # related models is not included in the endpoint
    ordering = ('modified_on', 'pk')

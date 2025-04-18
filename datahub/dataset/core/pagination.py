from rest_framework.pagination import CursorPagination


class DatasetCursorPagination(CursorPagination):
    """Cursor Pagination for dataset api endpoints."""

    ordering = ('created_on', 'pk')

    # We need to unset the pagination `offset_cutoff` value as we hit an issue
    # with pagination ordering when the model has many thousands of duplicate
    # `created_on` dates. Effectively, if the number of duplicate timestamps
    # is greater than the `offset_cutoff` the `next_page` in the response would
    # point to the current page creating an infinite loop.
    offset_cutoff = None

    # Allow clients to override the default page size (100) for paginated responses
    page_size_query_param = 'page_size'

    # Set a maximum page size that we'll allow, so clients can't do something
    # completely outrageous.
    max_page_size = 10_000

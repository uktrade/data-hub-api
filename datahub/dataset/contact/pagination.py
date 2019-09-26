from rest_framework.pagination import CursorPagination


class ContactsDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for ContactsDatasetView
    """

    ordering = ('id', 'created_on')
    page_size_query_param = 'page_size'

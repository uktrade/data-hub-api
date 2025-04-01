from rest_framework import pagination


class ContactPageSize(pagination.PageNumberPagination):
    """The default page_size is 100, this increases it to display more
    contacts on the frontend dropdown menu for companies with more than
    100 contacts.
    """

    page_size = 300

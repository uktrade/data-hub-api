from django.core.exceptions import ImproperlyConfigured
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class ActivityCursorPagination(CursorPagination):
    """
    Cursor pagination for activities.

    The activity stream service scrapes specified endpoints at regular intervals to get the
    activity feed from various services. It scrapes all the pages and more frequently: the
    last page only. If the last page has a "next" link, it scrapes that and updates the pointer
    to the last page.

    The default LIMIT-ORDER pagination gets slower as you progress through the pages so we
    decided to use cursor pagination here because we needed to render the last page quite
    frequently.

    According to the docs (See ref), cursor pagination required an ordering field that amongst
    other things:

        "Should be an unchanging value, such as a timestamp, slug, or other
        field that is only set once, on creation."

    Ref: https://www.django-rest-framework.org/api-guide/pagination/#cursorpagination
    """

    summary = None

    def _get_url(self):
        return self.encode_cursor(self.cursor) if self.cursor else self.base_url

    def _get_summary(self):
        if self.summary is None:
            raise ImproperlyConfigured(
                f'{self.__class__.__name__} requires definition of `summary` attribute '
                'or a `_get_summary()` method',
            )
        return self.summary

    def get_paginated_response(self, data):
        """
        Overriding this function to re-format the response according to
        activity stream spec.
        """
        return Response(
            {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'summary': self._get_summary(),
                'type': 'OrderedCollectionPage',
                'id': self._get_url(),
                'partOf': self.base_url,
                'orderedItems': data,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
        )

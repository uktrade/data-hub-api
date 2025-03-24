import binascii
import uuid
from base64 import b64decode
from datetime import datetime, timedelta
from urllib.parse import parse_qs, parse_qsl, urlencode, urlparse, urlunparse

from django.core.exceptions import ImproperlyConfigured
from django.db.models import F, Func, TextField
from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from rest_framework.settings import api_settings


class ActivityCursorPagination(BasePagination):
    """Cursor pagination for activities.

    The activity stream service scrapes specified endpoints at regular intervals to get the
    activity feed from various services. It scrapes all the pages and more frequently: the
    last page only. If the last page has a "next" link, it scrapes that and updates the pointer
    to the last page.

    The default LIMIT-ORDER pagination gets slower as you progress through the pages so we
    decided to use cursor pagination here because we needed to render the last page quite
    frequently.

    The built-in Django Rest Framework Cursor pagination is not used, since it

    - has a lot of code that isn't applicable to this use case, which makes it tricky to extend or
      debug, e.g. for peformance issues
    - uses an almost-unique value + offset cursor that isn't needed when we have a completely
      unique compound cursor: (modified_on, id)
    """

    page_size = api_settings.PAGE_SIZE
    summary = None

    def _get_summary(self):
        if self.summary is None:
            raise ImproperlyConfigured(
                f'{self.__class__.__name__} requires definition of `summary` attribute '
                'or a `_get_summary()` method',
            )
        return self.summary

    def _replace_query_param(self, url, key, vals):
        """Replaces all of the values of `key` of the query in `url` with `vals`

        The DRF version of this function is not used, since it always replaces all of the values of
        `key` with a single value.
        """
        parsed = urlparse(url)
        return urlunparse(parsed._replace(query=urlencode(tuple(
            (_key, val) for (_key, val) in parse_qsl(parsed.query, keep_blank_values=True)
            if _key != key
        ) + tuple((key, val) for val in vals))))

    def paginate_queryset(self, queryset, request, view=None):
        """Returns a page of results based on the cursor query string parameter. Designed to make the
        last page empty
        """
        # Extract cursor from query string. Inclues partial support for DRF's base64-encoded cursor
        # of timestamp + offset, the previous pagination mechanism. This is so that at the time
        # of deployment the Activity Stream can carry on from at most a few pages before where it
        # was. Once this is live and working, the DRF support can be removed
        try:
            after_ts_str = parse_qs(b64decode(request.GET.getlist('cursor')[0]))[b'p'][0].decode()
            after_id_str = '00000000-0000-0000-0000-000000000000'
        except (IndexError, KeyError, binascii.Error):
            after_ts_str, after_id_str = request.GET.getlist(
                'cursor',
                ('0001-01-01 00:00:00.000000+00:00', '00000000-0000-0000-0000-000000000000'),
            )

        after_ts = datetime.fromisoformat(after_ts_str)
        after_id = uuid.UUID(after_id_str)

        # Filter queryset to be after cursor.
        #
        # A composite/row/tuple lexicographic comparison is used to have the biggest chance of
        # fully using a multicolumn index. When tested on interactions in production, these queries
        # take ~50ms. If doing the comparison "manually", such queries take take ~1.5s+
        #
        # To do this in the Django ORM requires 'annotate', which itself requires a small hack: the
        # setting of an output_field, which can be anything since we don't access the value.
        modified_on_id = Func(F('modified_on'), F('id'), function='ROW', output_field=TextField())
        after_ts_id = Func(after_ts, after_id, function='ROW')

        # Mitigate the risk of timestamps being committed slightly out of order, which could result
        # in activities being missed when the last page is polled
        one_second_ago = datetime.now() - timedelta(seconds=1)

        page = list(queryset
                    .annotate(modified_on_id=modified_on_id)
                    .filter(modified_on_id__gt=after_ts_id, modified_on__lt=one_second_ago)
                    # Do not use ROW expressions in order_by: it seems to have an extremely
                    # negative performance impact
                    .order_by('modified_on', 'id')[:self.page_size])

        # Build and store next link for all non-empty pages to be used in get_paginated_response
        if not page:
            self.next_link = None
        else:
            final_instance = page[-1]
            next_after_ts_str = final_instance.modified_on.isoformat(timespec='microseconds')
            next_after_id_str = str(final_instance.id)
            self.next_link = self._replace_query_param(
                request.build_absolute_uri(),
                'cursor', (next_after_ts_str, next_after_id_str),
            )

        return page

    def get_paginated_response(self, data):
        """Overriding this function to re-format the response according to
        activity stream spec.
        """
        return Response(
            {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'summary': self._get_summary(),
                'type': 'OrderedCollectionPage',
                'orderedItems': data,
                'next': self.next_link,
            },
        )

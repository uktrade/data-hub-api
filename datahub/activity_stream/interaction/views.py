from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

from config.settings.types import HawkScope
from datahub.activity_stream.interaction.serializers import InteractionActivitySerializer
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.viewsets import CoreViewSet
from datahub.interaction.queryset import get_base_interaction_queryset


class InteractionCursorPagination(CursorPagination):
    """
    Cursor pagination for interaction.

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

    `modified_on` is no unchanging but we have decided to use it because the benefits of being
    able to generate the last page of interactions in under 10s far outweigh the fact that
    sometimes the last page will not contain all the updates.

    Ref: https://www.django-rest-framework.org/api-guide/pagination/#cursorpagination
    """

    ordering = ('modified_on', 'pk')

    def _get_url(self):
        return self.encode_cursor(self.cursor) if self.cursor else self.base_url

    def get_paginated_response(self, data):
        """
        Override this function to re-format the response according to
        activity stream spec.
        """
        return Response(
            {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'summary': 'Interaction Activities',
                'type': 'OrderedCollectionPage',
                'id': self._get_url(),
                'partOf': self.base_url,
                'orderedItems': data,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
        )


class InteractionActivityViewSet(HawkResponseSigningMixin, CoreViewSet):
    """
    Interaction ViewSet for the activity stream
    """

    authentication_classes = (HawkAuthentication,)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.activity_stream
    pagination_class = InteractionCursorPagination
    serializer_class = InteractionActivitySerializer
    queryset = get_base_interaction_queryset()

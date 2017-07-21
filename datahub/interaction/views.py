from django_filters.rest_framework import DjangoFilterBackend

from datahub.core.viewsets import CoreViewSetV1
from datahub.interaction.queryset import get_interaction_queryset
from datahub.interaction.serializers import (
    InteractionSerializerRead,
    InteractionSerializerWrite,
)


class InteractionViewSetV1(CoreViewSetV1):
    """Interaction ViewSet."""

    read_serializer_class = InteractionSerializerRead
    write_serializer_class = InteractionSerializerWrite
    # It's difficult to include everything in select_related() and prefetch_related()
    # because of the excessive nesting in this v1 endpoint.
    queryset = get_interaction_queryset()
    filter_backends = (
        DjangoFilterBackend,
    )
    filter_fields = ['company_id', 'contact_id', 'investment_project_id']

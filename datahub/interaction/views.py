from django_filters.rest_framework import DjangoFilterBackend

from datahub.core.viewsets import CoreViewSetV1
from datahub.interaction.models import Interaction
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
    queryset = Interaction.objects.select_related(
        'company',
        'contact',
        'dit_adviser',
        'dit_team',
        'interaction_type',
        'service',
        'contact__company',
        'investment_project__investor_company',
    )
    filter_backends = (
        DjangoFilterBackend,
    )
    filter_fields = ['company_id', 'contact_id', 'investment_project_id']

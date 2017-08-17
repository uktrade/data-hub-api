from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from datahub.core.viewsets import CoreViewSetV1, CoreViewSetV3
from datahub.interaction.queryset import get_interaction_queryset_v1, get_interaction_queryset_v3
from datahub.interaction.serializers import (
    InteractionSerializerReadV1, InteractionSerializerV3, InteractionSerializerWriteV1,
)


class InteractionViewSetV1(CoreViewSetV1):
    """Interaction ViewSet."""

    read_serializer_class = InteractionSerializerReadV1
    write_serializer_class = InteractionSerializerWriteV1
    # It's difficult to include everything in select_related() and prefetch_related()
    # because of the excessive nesting in this v1 endpoint.
    queryset = get_interaction_queryset_v1()
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filter_fields = ['company_id', 'contact_id', 'investment_project_id']
    ordering_fields = ('date', 'created_on')
    ordering = ('-date', '-created_on')


class InteractionViewSetV3(CoreViewSetV3):
    """Interaction ViewSet v3."""

    serializer_class = InteractionSerializerV3
    queryset = get_interaction_queryset_v3()
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filter_fields = ['company_id', 'contact_id', 'investment_project_id']
    ordering_fields = ('date', 'created_on')
    ordering = ('-date', '-created_on')

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from datahub.core.viewsets import CoreViewSetV3
from datahub.interaction.queryset import get_interaction_queryset_v3
from datahub.interaction.serializers import InteractionSerializerV3
from datahub.oauth.scopes import Scope


class InteractionViewSetV3(CoreViewSetV3):
    """Interaction ViewSet v3."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = InteractionSerializerV3
    queryset = get_interaction_queryset_v3()
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filter_fields = ['company_id', 'contact_id', 'investment_project_id']
    ordering_fields = ('date', 'created_on')
    ordering = ('-date', '-created_on')

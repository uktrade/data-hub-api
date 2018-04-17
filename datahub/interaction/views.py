from django_filters.rest_framework import DjangoFilterBackend
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.filters import OrderingFilter

from datahub.core.viewsets import CoreViewSet
from datahub.interaction.permissions import (
    InteractionModelPermissions,
    IsAssociatedToInvestmentProjectInteractionFilter,
    IsAssociatedToInvestmentProjectInteractionPermission,
)
from datahub.interaction.queryset import get_interaction_queryset
from datahub.interaction.serializers import InteractionSerializer
from datahub.oauth.scopes import Scope


class InteractionViewSet(CoreViewSet):
    """Interaction ViewSet v3."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        InteractionModelPermissions,
        IsAssociatedToInvestmentProjectInteractionPermission,
    )
    serializer_class = InteractionSerializer
    queryset = get_interaction_queryset()
    filter_backends = (
        DjangoFilterBackend,
        IsAssociatedToInvestmentProjectInteractionFilter,
        OrderingFilter,
    )
    filter_fields = ['company_id', 'contact_id', 'investment_project_id']
    ordering_fields = ('date', 'created_on')
    ordering = ('-date', '-created_on')

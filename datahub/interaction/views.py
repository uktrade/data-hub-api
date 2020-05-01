from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.interaction.permissions import (
    InteractionModelPermissions,
    IsAssociatedToInvestmentProjectInteractionFilter,
    IsAssociatedToInvestmentProjectInteractionPermission,
)
from datahub.interaction.queryset import get_interaction_queryset
from datahub.interaction.serializers import InteractionSerializer


class InteractionViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Interaction ViewSet v3."""

    permission_classes = (
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
    filterset_fields = [
        'company_id',
        'contacts__id',
        'event_id',
        'investment_project_id',
    ]
    ordering_fields = (
        'company__name',
        'created_on',
        'date',
        'first_name_of_first_contact',
        'last_name_of_first_contact',
        'subject',
    )
    ordering = ('-date', '-created_on')

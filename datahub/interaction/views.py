from collections import OrderedDict

from django_filters import CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet

from datahub.core.viewsets import CoreViewSetV1, CoreViewSetV2
from datahub.interaction.models import Interaction, ServiceDelivery
from datahub.interaction.serializers import (
    InteractionSerializerRead,
    InteractionSerializerWrite,
    ServiceDeliverySerializerV2
)


class InteractionViewSetV1(CoreViewSetV1):
    """Interaction ViewSet."""

    read_serializer_class = InteractionSerializerRead
    write_serializer_class = InteractionSerializerWrite
    queryset = Interaction.objects.select_related(
        'interaction_type',
        'dit_advisor',
        'company',
        'contact'
    ).all()

    def create(self, request, *args, **kwargs):
        """Override create to inject the user from session."""
        request.data.update({'dit_advisor': str(request.user.pk)})
        return super().create(request, *args, **kwargs)


class ServiceDeliveryFilter(FilterSet):
    """Service delivery filter."""

    company = CharFilter(name='company__pk', lookup_expr='exact')
    contact = CharFilter(name='contact__pk', lookup_expr='exact')

    class Meta:  # noqa: D101
        model = ServiceDelivery
        fields = ['company', 'contact']


class ServiceDeliveryViewSetV2(CoreViewSetV2):
    """Service delivery viewset."""

    def create(self, request, *args, **kwargs):
        """Override create to inject the user from session."""
        request.data.update({
            'dit_advisor': OrderedDict([
                ('type', 'Advisor'), ('id', str(request.user.pk))
            ])
        })
        return super().create(request, *args, **kwargs)

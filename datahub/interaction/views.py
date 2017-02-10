from datahub.core.viewsets import CoreViewSetV1, CoreViewSetV2
from datahub.interaction.models import Interaction, ServiceDelivery
from datahub.interaction.serializers import (InteractionSerializerRead,
                                             InteractionSerializerWrite,
                                             ServiceDeliverySerializerV2)


class InterceptUserMixin:
    """Add the user to the model instance."""

    def create(self, request, *args, **kwargs):
        """Override create to inject the user from session."""
        request.data.update({'dit_advisor': str(request.user.pk)})
        return super().create(request, *args, **kwargs)


class InteractionViewSetV1(InterceptUserMixin, CoreViewSetV1):
    """Interaction ViewSet."""

    read_serializer_class = InteractionSerializerRead
    write_serializer_class = InteractionSerializerWrite
    queryset = Interaction.objects.select_related(
        'interaction_type',
        'dit_advisor',
        'company',
        'contact'
    ).all()


class ServiceDeliveryViewSetV2(InterceptUserMixin, CoreViewSetV2):
    """Service delivery viewset."""

    serializer_class = ServiceDeliverySerializerV2
    queryset = ServiceDelivery.objects.all()

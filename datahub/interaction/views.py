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
    queryset = Interaction.objects.select_related(
        'interaction_type',
        'dit_advisor',
        'company',
        'contact'
    ).all()

    def get_additional_data(self, update):
        """Override create to inject the user from session."""
        data = super().get_additional_data(update)
        data['dit_advisor'] = self.request.user
        return data

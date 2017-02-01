from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.interaction.models import Interaction
from datahub.interaction.serializers import InteractionSerializerRead, InteractionSerializerWrite


class InteractionViewSet(ArchivableViewSetMixin, CoreViewSet):
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

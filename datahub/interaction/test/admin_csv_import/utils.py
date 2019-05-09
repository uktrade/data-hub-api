from datahub.core.test_utils import random_obj_for_queryset
from datahub.interaction.models import CommunicationChannel
from datahub.metadata.models import Service


def random_communication_channel(disabled=False):
    """Get a random communication channel."""
    return random_obj_for_queryset(
        CommunicationChannel.objects.filter(disabled_on__isnull=not disabled),
    )


def random_service(disabled=False):
    """Get a random service."""
    return random_obj_for_queryset(
        Service.objects.filter(disabled_on__isnull=not disabled),
    )

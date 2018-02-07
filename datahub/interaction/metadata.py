from datahub.interaction import models
from datahub.metadata.fixtures import Fixture
from datahub.metadata.registry import registry


class InteractionFixtures(Fixture):
    """Metadata fixtures (for the loadinitialmetadata command)."""

    files = [
        'fixtures/communication_channels.yaml'
    ]


registry.register(
    metadata_id='communication-channel',
    model=models.CommunicationChannel,
)

registry.register(
    metadata_id='service-delivery-status',
    model=models.ServiceDeliveryStatus,
)

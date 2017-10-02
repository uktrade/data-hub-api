from datahub.interaction import models
from datahub.metadata.registry import registry


registry.register(
    metadata_id='communication-channel',
    model=models.CommunicationChannel,
)

# For backwards compatibility. Will be removed once front end updated.
registry.register(
    metadata_id='interaction-type',
    model=models.CommunicationChannel,
)

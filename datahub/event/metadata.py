from datahub.event import models
from datahub.metadata.registry import registry


registry.register(
    metadata_id='programme',
    model=models.Programme,
)

registry.register(
    metadata_id='event-type',
    model=models.EventType,
)

registry.register(
    metadata_id='location-type',
    model=models.LocationType,
)

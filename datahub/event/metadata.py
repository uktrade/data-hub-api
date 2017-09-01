from datahub.event import models
from datahub.metadata.registry import registry


registry.register(
    metadata_id='programme',
    model=models.Programme,
)

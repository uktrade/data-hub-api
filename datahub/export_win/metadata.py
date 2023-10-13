from datahub.export_win import models
from datahub.metadata.registry import registry


registry.register(
    metadata_id='team-type',
    model=models.TeamType,
)

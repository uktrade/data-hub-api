from datahub.investment.opportunity import models
from datahub.metadata.registry import registry

PATH_PREFIX = 'large-capital-opportunity'


registry.register(
    metadata_id='opportunity-status',
    model=models.OpportunityStatus,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='opportunity-type',
    model=models.OpportunityType,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='opportunity-value-type',
    model=models.OpportunityValueType,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='abandonment-reason',
    model=models.AbandonmentReason,
    path_prefix=PATH_PREFIX,
)

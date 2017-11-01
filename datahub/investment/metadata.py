from datahub.investment import models
from datahub.metadata.registry import registry


registry.register(
    metadata_id='investment-specific-programme',
    model=models.SpecificProgramme,
)

registry.register(
    metadata_id='investment-investor-type',
    model=models.InvestorType,
)

registry.register(
    metadata_id='investment-involvement',
    model=models.Involvement,
)

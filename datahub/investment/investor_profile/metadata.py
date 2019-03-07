from datahub.investment.investor_profile import models
from datahub.investment.investor_profile.serializers import AssetClassInterestSerializer
from datahub.metadata.registry import registry

PATH_PREFIX = 'capital-investment'


registry.register(
    metadata_id='asset-class-interest',
    model=models.AssetClassInterest,
    serializer=AssetClassInterestSerializer,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='required-checks-conducted',
    model=models.RequiredChecksConducted,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='construction-risk',
    model=models.ConstructionRisk,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='deal-ticket-size',
    model=models.DealTicketSize,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='desired-deal-role',
    model=models.DesiredDealRole,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='equity-percentage',
    model=models.EquityPercentage,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='investor-type',
    model=models.InvestorType,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='large-capital-investment-type',
    model=models.LargeCapitalInvestmentType,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='restriction',
    model=models.Restriction,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='return-rate',
    model=models.ReturnRate,
    path_prefix=PATH_PREFIX,
)

registry.register(
    metadata_id='time-horizon',
    model=models.TimeHorizon,
    path_prefix=PATH_PREFIX,
)

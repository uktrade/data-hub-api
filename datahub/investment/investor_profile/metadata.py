from datahub.investment.investor_profile import models
from datahub.investment.investor_profile.serializers import AssetClassInterestSerializer
from datahub.metadata.registry import registry


registry.register(
    metadata_id='asset-class-interest',
    model=models.AssetClassInterest,
    serializer=AssetClassInterestSerializer,
)

registry.register(
    metadata_id='required-checks-conducted',
    model=models.RequiredChecksConducted,
)

registry.register(
    metadata_id='construction-risk',
    model=models.ConstructionRisk,
)

registry.register(
    metadata_id='deal-ticket-size',
    model=models.DealTicketSize,
)

registry.register(
    metadata_id='desired-deal-role',
    model=models.DesiredDealRole,
)

registry.register(
    metadata_id='equity-percentage',
    model=models.EquityPercentage,
)

registry.register(
    metadata_id='large-capital-investor-type',
    model=models.InvestorType,
)

registry.register(
    metadata_id='large-capital-investment-type',
    model=models.LargeCapitalInvestmentType,
)

registry.register(
    metadata_id='restriction',
    model=models.Restriction,
)

registry.register(
    metadata_id='return-rate',
    model=models.ReturnRate,
)

registry.register(
    metadata_id='time-horizon',
    model=models.TimeHorizon,
)

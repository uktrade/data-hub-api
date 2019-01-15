from datahub.investment import models
from datahub.metadata.fixtures import Fixture
from datahub.metadata.registry import registry


class InvestmentFixtures(Fixture):
    """Metadata fixtures (for the loadinitialmetadata command)."""

    files = [
        'fixtures/investor_types.yaml',
        'fixtures/involvements.yaml',
        'fixtures/specific_programmes.yaml',
    ]


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

registry.register(
    metadata_id='investment-delivery-partner',
    model=models.InvestmentDeliveryPartner,
)


registry.register(
    metadata_id='likelihood-to-land',
    model=models.LikelihoodToLand,
)

registry.register(
    metadata_id='project-manager-request-status',
    model=models.ProjectManagerRequestStatus,
)

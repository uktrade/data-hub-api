from datahub.interaction import models
from datahub.metadata.registry import registry


registry.register(
    metadata_id='communication-channel',
    model=models.CommunicationChannel,
)

registry.register(
    metadata_id='service-delivery-status',
    model=models.ServiceDeliveryStatus,
)

registry.register(
    metadata_id='policy-area',
    model=models.PolicyArea,
)

registry.register(
    metadata_id='policy-issue-type',
    model=models.PolicyIssueType,
)

registry.register(
    metadata_id='expert-advice-topic',
    model=models.ExportAdviceTopic,
)

registry.register(
    metadata_id='investment-advice-tooic',
    model=models.InvestmentAdviceTopic,
)

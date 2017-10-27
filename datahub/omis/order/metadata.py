from datahub.core.serializers import ConstantModelSerializer
from datahub.metadata.registry import registry

from . import models


registry.register(
    metadata_id='order-service-type',
    model=models.ServiceType,
    serializer=ConstantModelSerializer
)

registry.register(
    metadata_id='order-cancellation-reason',
    model=models.CancellationReason,
    serializer=ConstantModelSerializer
)

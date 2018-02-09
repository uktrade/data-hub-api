from datahub.core.serializers import ConstantModelSerializer
from datahub.metadata.fixtures import Fixture
from datahub.metadata.registry import registry

from . import models


class ServiceTypeFixtures(Fixture):
    """Metadata fixtures (for the loadinitialmetadata command)."""

    files = [
        'fixtures/service_types.yaml'
    ]


class CancellationReasonFixtures(Fixture):
    """Metadata fixtures (for the loadinitialmetadata command)."""

    files = [
        'fixtures/cancellation_reasons.yaml'
    ]


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

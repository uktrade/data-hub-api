from datahub.metadata.registry import registry

from . import models
from .serializers import ServiceTypeSerializer


registry.register(
    metadata_id='order-service-type',
    model=models.ServiceType,
    serializer=ServiceTypeSerializer
)

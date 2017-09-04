from datahub.metadata.registry import registry

from . import models
from .serializers import MarketSerializer


registry.register(
    metadata_id='omis-market',
    model=models.Market,
    queryset=models.Market.objects.select_related('country').order_by('country__name'),
    serializer=MarketSerializer
)

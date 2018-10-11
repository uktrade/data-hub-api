from datahub.metadata.fixtures import Fixture
from datahub.metadata.registry import registry
from datahub.omis.market import models
from datahub.omis.market.serializers import MarketSerializer


class MarketFixtures(Fixture):
    """Metadata fixtures (for the loadinitialmetadata command)."""

    files = [
        'fixtures/markets.yaml',
    ]


registry.register(
    metadata_id='omis-market',
    model=models.Market,
    queryset=models.Market.objects.select_related('country').order_by('country__name'),
    serializer=MarketSerializer,
)

import pytest

from datahub.omis.market.models import Market
from datahub.omis.market.serializers import MarketSerializer


pytestmark = pytest.mark.django_db


def test_market_response():
    """Test the market serializer response data."""
    market = Market.objects.order_by('?').first()
    serializer = MarketSerializer(market)

    assert serializer.data == {
        'id': market.country.pk,
        'name': market.country.name,
        'disabled_on': market.disabled_on,
    }

import pytest

from ..models import Market
from ..serializers import MarketSerializer


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

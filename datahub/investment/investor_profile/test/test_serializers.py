import pytest

from datahub.investment.investor_profile.serializers import LargeCapitalInvestorProfileSerializer
from datahub.investment.investor_profile.test.factories import (
    CompleteLargeCapitalInvestorProfileFactory,
)

pytestmark = pytest.mark.django_db


class TestLargeCapitalInvestorProfileSerializer:
    """Tests for LargeCapitalInvestorProfileSerializer."""

    @pytest.mark.parametrize(
        'field,empty_value,expected_value',
        (
            ('global_assets_under_management', None, None),
            ('investable_capital', None, None),
            ('investor_type', '', None),
            ('investor_type', None, None),
            ('deal_ticket_sizes', [], []),
            ('investment_types', [], []),
            ('minimum_return_rate', '', None),
            ('time_horizons', [], []),
            ('restrictions', [], []),
            ('construction_risks', [], []),
            ('minimum_equity_percentage', '', None),
            ('desired_deal_roles', [], []),
            ('uk_region_locations', [], []),
            ('other_countries_being_considered', [], []),
            ('asset_classes_of_interest', [], []),
            ('notes_on_locations', '', ''),
        ),
    )
    def test_validate_fields_allow_null(self, field, empty_value, expected_value):
        """Test validates fields allow null or empty values."""
        profile = CompleteLargeCapitalInvestorProfileFactory()
        serializer = LargeCapitalInvestorProfileSerializer(
            data={field: empty_value},
            instance=profile,
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data[field] == expected_value

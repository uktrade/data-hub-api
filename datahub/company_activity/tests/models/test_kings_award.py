import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from freezegun import freeze_time

from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.models import KingsAwardRecipient
from datahub.company_activity.tests.factories import KingsAwardRecipientFactory

pytestmark = pytest.mark.django_db


class TestKingsAwardRecipientModel:
    """Tests for the KingsAwardRecipient model."""

    def test_str_representation(self):
        """Test the string representation of the model."""
        award = KingsAwardRecipientFactory(
            company__name='Test Company Ltd',
            year_awarded=2025,
            category=KingsAwardRecipient.Category.INNOVATION,
        )
        assert str(award) == 'Test Company Ltd - 2025 Innovation (Technology)'

    @pytest.mark.parametrize(
        ('alias', 'expected_category'),
        [
            ('international-trade', KingsAwardRecipient.Category.INTERNATIONAL_TRADE),
            ('innovation', KingsAwardRecipient.Category.INNOVATION),
            ('export-and-technology', KingsAwardRecipient.Category.EXPORT_AND_TECHNOLOGY),
            ('sustainable-development', KingsAwardRecipient.Category.SUSTAINABLE_DEVELOPMENT),
            ('promoting-opportunity', KingsAwardRecipient.Category.PROMOTING_OPPORTUNITY),
            ('International-TRADE', KingsAwardRecipient.Category.INTERNATIONAL_TRADE),
            ('INNOVATION', KingsAwardRecipient.Category.INNOVATION),
        ],
    )
    def test_category_from_alias_valid(self, alias, expected_category):
        """Test Category.from_alias with valid aliases."""
        assert KingsAwardRecipient.Category.from_alias(alias) == expected_category

    @pytest.mark.parametrize(
        'alias',
        [
            'invalid-alias',
            'trade',
            '',
        ],
    )
    def test_category_from_alias_invalid(self, alias):
        """Test Category.from_alias raises ValueError for invalid aliases."""
        with pytest.raises(ValueError, match='Invalid category alias:'):
            KingsAwardRecipient.Category.from_alias(alias)

    def test_unique_together_constraint(self):
        """Test that a company cannot receive the same award category in the same year twice."""
        award = KingsAwardRecipientFactory()
        with pytest.raises(IntegrityError):
            KingsAwardRecipientFactory(
                company=award.company,
                category=award.category,
                year_awarded=award.year_awarded,
            )

    @freeze_time('2025-04-01')
    @pytest.mark.parametrize(
        ('year_awarded', 'year_expired', 'is_valid'),
        [
            (2025, 2030, True),  # valid case
            (1966, 1971, True),  # minimum valid year
            (2026, 2031, True),  # max awarded/expired year lookahead
            (2027, 2031, False),  # awarded year too far ahead
            (2026, 2032, False),  # expired year too far ahead
            (1965, 1970, False),  # awarded year before minimum
            (2023, 1970, False),  # expired year before minimum
            (2023, 2022, False),  # expired year before awarded year
        ],
    )
    def test_year_validation(self, year_awarded, year_expired, is_valid):
        """Test the custom year validation in the clean method."""
        award = KingsAwardRecipient(
            company=CompanyFactory(),
            category=KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
            year_awarded=year_awarded,
            year_expired=year_expired,
        )
        if is_valid:
            try:
                award.full_clean()
            except ValidationError as e:
                pytest.fail(f'Validation failed unexpectedly: {e.message_dict}')
        else:
            with pytest.raises(ValidationError):
                award.full_clean()

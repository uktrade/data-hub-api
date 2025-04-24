import pytest
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company_activity.models import KingsAwardRecipient
from datahub.company_activity.tests.factories import KingsAwardRecipientFactory
from datahub.core.test_utils import APITestMixin

pytestmark = pytest.mark.django_db


class TestKingsAwardRecipientViewSet(APITestMixin):
    """Tests for the KingsAwardRecipientViewSet."""

    endpoint = reverse('api-v4:company-activity:kings-award:collection')

    def test_list_awards_authenticated(self):
        """Test listing awards."""
        awards = KingsAwardRecipientFactory.create_batch(3)
        response = self.api_client.get(self.endpoint)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        assert len(response_data['results']) == 3

        expected_ids = [
            str(award.id)
            for award in sorted(awards, key=lambda x: (-x.year_awarded, x.company.name))
        ]
        actual_ids = [result['id'] for result in response_data['results']]
        assert actual_ids == expected_ids

    @pytest.mark.parametrize(
        ('year_awarded_filter', 'expected_count'),
        [
            ('2022', 0),
            ('2024', 2),
            ('2025', 1),
            ('2022,2024', 2),
            ('2023,2024', 3),
            ('2022,2023,2024,2025', 4),
        ],
    )
    def test_filter_by_year_awarded(self, year_awarded_filter, expected_count):
        """Test filtering by year_awarded."""
        KingsAwardRecipientFactory(year_awarded=2023)
        KingsAwardRecipientFactory(year_awarded=2024)
        KingsAwardRecipientFactory(year_awarded=2024)
        KingsAwardRecipientFactory(year_awarded=2025)

        params = urlencode({'year_awarded': year_awarded_filter})
        url = f'{self.endpoint}?{params}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == expected_count

    @pytest.mark.parametrize(
        ('category_filter', 'expected_count', 'expected_categories'),
        [
            (
                'innovation',
                2,
                {KingsAwardRecipient.Category.INNOVATION},
            ),
            (
                'international-trade',
                1,
                {KingsAwardRecipient.Category.INTERNATIONAL_TRADE},
            ),
            (
                'innovation,international-trade',
                3,
                {
                    KingsAwardRecipient.Category.INNOVATION,
                    KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
                },
            ),
            (
                'INNOVATION,international-trade',  # mixed case
                3,
                {
                    KingsAwardRecipient.Category.INNOVATION,
                    KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
                },
            ),
            (
                'promoting-opportunity',
                0,
                set(),
            ),
            (
                ' innovation , international-trade ',  # with whitespace
                3,
                {
                    KingsAwardRecipient.Category.INNOVATION,
                    KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
                },
            ),
        ],
    )
    def test_filter_by_category_alias(self, category_filter, expected_count, expected_categories):
        """Test filtering by category alias."""
        KingsAwardRecipientFactory.create_batch(
            2,
            category=KingsAwardRecipient.Category.INNOVATION,
        )
        KingsAwardRecipientFactory(category=KingsAwardRecipient.Category.INTERNATIONAL_TRADE)
        KingsAwardRecipientFactory(category=KingsAwardRecipient.Category.SUSTAINABLE_DEVELOPMENT)

        params = urlencode({'category': category_filter})
        url = f'{self.endpoint}?{params}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == expected_count

        result_categories = {
            next(k for k, v in KingsAwardRecipient.Category.choices if v == result['category'])
            for result in response_data['results']
        }
        assert result_categories == expected_categories

    @pytest.mark.parametrize(
        ('category_filter', 'expected_error_detail'),
        [
            (
                'invalid-alias',
                'Invalid category alias(es): invalid-alias. Valid aliases are: '
                'international-trade, innovation, export-and-technology, '
                'sustainable-development, promoting-opportunity.',
            ),
            (
                'innovation,invalid-alias,another-invalid',
                'Invalid category alias(es): invalid-alias, another-invalid. Valid aliases are: '
                'international-trade, innovation, export-and-technology, '
                'sustainable-development, promoting-opportunity.',
            ),
            (
                '',  # empty string should return all
                None,
            ),
            (
                ', , ',  # phantom commas should return all
                None,
            ),
        ],
    )
    def test_filter_by_category_alias_invalid(self, category_filter, expected_error_detail):
        """Test filtering by invalid category alias raises ValidationError."""
        KingsAwardRecipientFactory.create_batch(
            2,
            category=KingsAwardRecipient.Category.INNOVATION,
        )
        params = urlencode({'category': category_filter})
        url = f'{self.endpoint}?{params}'
        response = self.api_client.get(url)

        if expected_error_detail:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            response_data = response.json()
            assert response_data == [expected_error_detail]
        else:
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data['count'] == 2

from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from datahub.company.serializers import ContactV4Serializer
from datahub.company.test.factories import CompanyFactory
from datahub.core import constants

# mark the whole module for db use
pytestmark = pytest.mark.django_db

FROZEN_TIME = '2020-03-13T14:21:24.367265+00:00'

request = Mock(
    headers={
        'x-b3-traceid': '123',
        'x-b3-spanid': '456',
    },
)


@freeze_time(FROZEN_TIME)
class TestContactV4Serializer:
    """Tests for the Contact V4 Serializer."""

    @pytest.mark.parametrize(
        ('country_id', 'expected_response', 'is_valid', 'address_area'),
        [
            (
                constants.Country.united_states.value.id,
                {
                    'address_area': ['This field is required.'],
                },
                False,
                None,
            ),
            (
                constants.Country.canada.value.id,
                {
                    'address_area': ['This field is required.'],
                },
                False,
                None,
            ),
            (
                constants.Country.canada.value.id,
                {},
                True,
                {
                    'id': constants.AdministrativeArea.quebec.value.id,
                    'name': constants.AdministrativeArea.quebec.value.name,
                },
            ),
            (
                constants.Country.united_kingdom.value.id,
                {},
                True,
                None,
            ),
        ],
    )
    def test_area_required_validation_on_respective_countries(
        self,
        country_id,
        expected_response,
        is_valid,
        address_area,
    ):
        """Ensure that area required validation is called for appropriate countries
        and excluded for others.
        """
        company = CompanyFactory()
        data = {
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
            },
            'first_name': 'Jane',
            'last_name': 'Doe',
            'company': {
                'id': str(company.pk),
            },
            'primary': True,
            'email': 'foo@bar.com',
            'full_telephone_number': '+44123456789',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_town': 'Bar',
            'address_country': {
                'id': country_id,
            },
            'address_area': address_area,
        }
        contact_serializer = ContactV4Serializer(data=data, context={'request': request})
        assert contact_serializer.is_valid(raise_exception=False) is is_valid
        assert len(contact_serializer.errors) == len(expected_response)
        assert contact_serializer.errors == expected_response

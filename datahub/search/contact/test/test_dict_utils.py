import pytest

from datahub.core.test_utils import construct_mock
from datahub.search.contact import dict_utils


@pytest.mark.parametrize(
    'obj,field_name,expected_output',
    (
        # address_same_as_company = False and char field
        (
            construct_mock(
                address_same_as_company=False,
                address_1='2',
            ),
            'address_1',
            '2',
        ),

        # address_same_as_company = False and nested field
        (
            construct_mock(
                address_same_as_company=False,
                address_country=construct_mock(
                    id='80756b9a-5d95-e211-a939-e4115bead28a',
                    name='United Kingdom',
                ),
            ),
            'address_country',
            {
                'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                'name': 'United Kingdom',
            },
        ),

        # address_same_as_company = True and char field
        (
            construct_mock(
                address_same_as_company=True,
                address_1='2',
                company=construct_mock(
                    address_1='3',
                ),
            ),
            'address_1',
            '3',
        ),

        # address_same_as_company = True and nested field
        (
            construct_mock(
                address_same_as_company=True,
                address_country=construct_mock(
                    id='80756b9a-5d95-e211-a939-e4115bead28a',
                    name='United Kingdom',
                ),
                company=construct_mock(
                    address_country=construct_mock(
                        id='81756b9a-5d95-e211-a939-e4115bead28a',
                        name='United States',
                    ),
                ),
            ),
            'address_country',
            {
                'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                'name': 'United States',
            },
        ),
    ),
)
def test_computed_address_field(obj, field_name, expected_output):
    """Tests for computed_address_field."""
    actual_output = dict_utils.computed_address_field(field_name)(obj)

    assert actual_output == expected_output

import pytest

from datahub.company.notify import (
    get_dnb_investigation_context,
)
from datahub.company.test.factories import CompanyFactory


@pytest.mark.parametrize(
    'investigation_data',
    (
        None,
        {},
        {'foo': 'bar'},
        {'telephone_number': '12345678'},
        {'telephone_number': None},
    ),
)
def test_get_dnb_investigation_context(investigation_data):
    """
    Test if get_dnb_investigation_context returns a dict with sensible
    values for the required fields.
    """
    company = CompanyFactory(dnb_investigation_data=investigation_data)
    investigation_data = investigation_data or {}
    address_parts = [
        company.address_1,
        company.address_2,
        company.address_town,
        company.address_county,
        company.address_country.name,
        company.address_postcode,
    ]
    expected_address = ', '.join(
        address_part for address_part in address_parts if address_part
    )
    assert get_dnb_investigation_context(company) == {
        'business_name': company.name,
        'business_address': expected_address,
        'website': company.website or '',
        'contact_number': investigation_data.get('telephone_number') or '',
    }

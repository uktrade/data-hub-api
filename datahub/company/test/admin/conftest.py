import pytest


@pytest.fixture
def dnb_response():
    """
    Minimal valid DNB response
    """
    return {
        'results': [
            {
                'address_line_1': '10 Fake Drive',
                'address_line_2': '',
                'address_postcode': 'AB0 1CD',
                'address_town': 'London',
                'address_county': '',
                'address_country': 'GB',
                'registered_address_line_1': '11 Fake Drive',
                'registered_address_line_2': '',
                'registered_address_postcode': 'AB0 2CD',
                'registered_address_town': 'London',
                'registered_address_county': '',
                'registered_address_country': 'GB',
                'domain': 'foo.com',
                'duns_number': '123456789',
                'primary_name': 'FOO BICYCLES LIMITED',
                'trading_names': [],
                'registration_numbers': [
                    {
                        'registration_number': '012345',
                        'registration_type': 'uk_companies_house_number',
                    },
                ],
                'global_ultimate_duns_number': '987654321',
            },
        ],
    }

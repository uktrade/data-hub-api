import pytest

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.dnb_api.serializers import (
    DNBCompanySerializer,
    SerializerNotPartial,
)


override_functions = (
    pytest.param(
        lambda data, null_keys: {k: v for k, v in data.items() if k not in null_keys},
        id='no-keys-for-null-values',
    ),
    pytest.param(
        lambda data, null_keys: {**data, **{k: None for k in null_keys}},
        id='null-values-for-null-values',
    ),
    pytest.param(
        lambda data, null_keys: {**data, **{k: '' for k in null_keys}},
        id='blank-for-null-values',
    ),
)


# def assert_company_data(company, data):
#     """
#     Check if each field of the given company has the same value as given data.
#     """
#     assert company.name == data['name']
#     assert company.address_1 == data['address']['line_1']
#     assert company.address_2 == data['address']['line_2']
#     assert company.address_town == data['address']['town']
#     assert company.address_county == data['address']['county']
#     assert company.address_postcode == data['address']['postcode']
#     assert str(company.address_country.id) == data['address']['country']['id']
#     assert str(company.business_type.id) == data['business_type']
#     assert str(company.sector.id) == data['sector']
#     assert str(company.uk_region.id) == data['uk_region']
#
#     website = data.get('website')
#     if website not in (None, ''):
#         url = urlparse(website)
#         website = f'{url.scheme or "http"}://{url.path or url.netloc}'
#     assert company.website == website


def test_dnb_company_serializer_partial_save(db):
    """
    Test DNBCompanySerializer.partial_save() method.
    """
    dh_company = CompanyFactory()
    original_company = Company.objects.get(id=dh_company.id)
    serializer = DNBCompanySerializer(
        dh_company,
        data={'name': 'foobar'},
        partial=True,
    )
    serializer.is_valid()
    serializer.partial_save(duns_number='123456789')
    dh_company.refresh_from_db()
    assert dh_company.name == 'foobar'
    assert dh_company.duns_number == '123456789'
    assert dh_company.modified_on == original_company.modified_on


def test_dnb_company_serializer_partial_save_serializer_not_partial(db):
    """
    Test DNBCompanySerializer.partial_save() method raises an error when the
    serializer is not partial.
    """
    dh_company = CompanyFactory()
    serializer = DNBCompanySerializer(
        dh_company,
        data={'name': 'foobar'},
    )
    serializer.is_valid()
    with pytest.raises(SerializerNotPartial):
        serializer.partial_save(duns_number='123456789')

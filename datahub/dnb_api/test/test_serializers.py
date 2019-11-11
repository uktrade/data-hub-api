from urllib.parse import urlparse

import pytest

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.dnb_api.serializers import (
    DNBCompanyInvestigationSerializer,
    DNBCompanySerializer,
    SerializerNotPartial,
)
from datahub.dnb_api.utils import format_dnb_company_investigation


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


def assert_company_data(company, data):
    """
    Check if each field of the given company has the same value as given data.
    """
    assert company.name == data['name']
    assert company.dnb_investigation_data == data['dnb_investigation_data']
    assert company.address_1 == data['address']['line_1']
    assert company.address_2 == data['address']['line_2']
    assert company.address_town == data['address']['town']
    assert company.address_county == data['address']['county']
    assert company.address_postcode == data['address']['postcode']
    assert str(company.address_country.id) == data['address']['country']['id']
    assert str(company.business_type.id) == data['business_type']
    assert str(company.sector.id) == data['sector']
    assert str(company.uk_region.id) == data['uk_region']

    website = data.get('website')
    if website not in (None, ''):
        url = urlparse(website)
        website = f'{url.scheme or "http"}://{url.path or url.netloc}'
    assert company.website == website


@pytest.mark.parametrize(
    'investigation_payload_override',
    (
        # No override
        {},
        # URL without scheme
        {'website': 'www.test.com'},
        # URL with https scheme
        {'website': 'https://www.test.com'},
        # Telephone number with non-numeric characters
        {'telephone_number': '123ABC'},
        # Telephone number with non-alphanumeric characters
        {'telephone_number': '+(44)123#456'},
    ),
)
def test_investigation_serializer_valid(
        db,
        investigation_payload,
        investigation_payload_override,
):
    """
    Test if DNBCompanyInvestigationSerializer saves a Company record given
    a valid payload.
    """
    data = format_dnb_company_investigation(
        {
            **investigation_payload,
            **investigation_payload_override,
        },
    )
    serializer = DNBCompanyInvestigationSerializer(data=data)
    assert serializer.is_valid()

    company = serializer.save()
    company.refresh_from_db()
    assert_company_data(company, data)


@pytest.mark.parametrize(
    'investigation_payload_override',
    (
        # telephone_number can be null if we have a website
        {'telephone_number'},
        # Website can be null if we have telephone_number
        {'website'},
    ),
)
@pytest.mark.parametrize(
    'override_function',
    override_functions,
)
def test_investigation_serializer_null_fields_valid(
        db,
        investigation_payload,
        investigation_payload_override,
        override_function,
):
    """
    Test if DNBCompanyInvestigationSerializer saves a Company record given
    a valid payload.

    A valid payload has wither a valid URL for website or valid telephone_number:
    country_code and number.
    """
    data = format_dnb_company_investigation(
        override_function(
            investigation_payload,
            investigation_payload_override,
        ),
    )
    serializer = DNBCompanyInvestigationSerializer(data=data)
    assert serializer.is_valid()

    company = serializer.save()
    company.refresh_from_db()
    assert_company_data(company, data)


@pytest.mark.parametrize(
    'investigation_data_override',
    (
        {'dnb_investigation_data'},
    ),
)
@pytest.mark.parametrize(
    'override_function',
    override_functions,
)
def test_investigation_serializer_no_investigation_data_valid(
        db,
        investigation_payload,
        investigation_data_override,
        override_function,
):
    """
    Test if DNBCompanyInvestigationSerializer is valid without dnb_investigation_data
    """
    data = override_function(
        format_dnb_company_investigation(
            investigation_payload,
        ),
        investigation_data_override,
    )
    serializer = DNBCompanyInvestigationSerializer(data=data)
    assert serializer.is_valid()


@pytest.mark.parametrize(
    'investigation_payload_override',
    (
        {'website', 'telephone_number'},
    ),
)
@pytest.mark.parametrize(
    'override_function',
    override_functions,

)
def test_investigation_serializer_null_fields_invalid(
        db,
        investigation_payload,
        investigation_payload_override,
        override_function,
):
    """
    If website as well as telephone_number are not given, the serializer
    should return an error.
    """
    data = format_dnb_company_investigation(
        override_function(
            investigation_payload,
            investigation_payload_override,
        ),
    )
    serializer = DNBCompanyInvestigationSerializer(data=data)
    assert not serializer.is_valid()
    assert serializer.errors == {
        'non_field_errors': [
            'Either website or telephone_number must be provided.',
        ],
    }


@pytest.mark.parametrize(
    'investigation_payload_override, expected_error',
    (
        # If website is specified, it should be a valid URL
        (
            {'website': 'test'},
            {'website': ['Enter a valid URL.']},
        ),
        # Other fields that are required and enforced by CompanySerializer
        (
            {'name': None},
            {'name': ['This field may not be null.']},
        ),
        (
            {'business_type': None},
            {'business_type': ['This field is required.']},
        ),
        (
            {'address': None},
            {'address': ['This field may not be null.']},
        ),
        (
            {'sector': None},
            {'sector': ['This field is required.']},
        ),
        (
            {'uk_region': None},
            {'uk_region': ['This field is required.']},
        ),
    ),
)
def test_investigation_serializer_invalid(
        db,
        investigation_payload,
        investigation_payload_override,
        expected_error,
):
    """
    Test if DNBCompanyInvestigationSerializer fails given an invalid payload.
    """
    serializer = DNBCompanyInvestigationSerializer(
        data=format_dnb_company_investigation(
            {**investigation_payload, **investigation_payload_override},
        ),
    )
    assert not serializer.is_valid()
    assert serializer.errors == expected_error


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

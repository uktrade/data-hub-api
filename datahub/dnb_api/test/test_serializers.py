import pytest
from rest_framework.exceptions import ValidationError

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.dnb_api.serializers import (
    ChangeRequestSerializer,
    DNBCompanyHierarchySerializer,
    DNBCompanySerializer,
    SerializerNotPartialError,
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


def test_dnb_company_serializer_partial_save(db):
    """Test DNBCompanySerializer.partial_save() method."""
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


def test_dnb_change_request_serializer(db):
    """Test that dnb change requests serialize correctly."""
    change_request = ChangeRequestSerializer(data={'turnover_gbp': 200})
    change_request.is_valid()

    assert dict(change_request.validated_data) == {'annual_sales': 245.94621911242905}


def test_dnb_company_serializer_partial_save_serializer_not_partial(db):
    """Test DNBCompanySerializer.partial_save() method raises an error when the
    serializer is not partial.
    """
    dh_company = CompanyFactory()
    serializer = DNBCompanySerializer(
        dh_company,
        data={'name': 'foobar'},
    )
    serializer.is_valid()
    with pytest.raises(SerializerNotPartialError):
        serializer.partial_save(duns_number='123456789')


def test_duns_number_is_not_valid(db):
    """Tests that serializer is not valid when duns number is not provided."""
    serializer = DNBCompanyHierarchySerializer(
        {},
        data={'duns_number': None},
    )
    with pytest.raises(ValidationError):
        serializer.validate_duns_number(duns_number=None)

    assert not serializer.is_valid()


def test_duns_number_is_valid(db):
    """Tests that serializer is valid when duns number is provided."""
    dh_company = CompanyFactory(duns_number='123456789')
    serializer = DNBCompanyHierarchySerializer(
        dh_company,
        data={'duns_number': '123456789'},
    )
    assert serializer.is_valid()

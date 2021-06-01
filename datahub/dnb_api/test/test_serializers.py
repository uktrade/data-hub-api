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

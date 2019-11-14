import pytest
from django.db.utils import IntegrityError

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import APITestMixin


pytestmark = pytest.mark.django_db


class TestPendingDNBInvestigation(APITestMixin):
    """
    Test if the `pending_dnb_investigation` field is set to False
    when a comapny is created in DataHub.
    """

    def test_model(self):
        """
        Check if a newly created company has `pending_dnb_investigation`
        set to False.
        """
        company = CompanyFactory()
        assert not Company.objects.get(
            id=company.id,
        ).pending_dnb_investigation

    def test_model_null(self):
        """
        Check if trying to create a new company that has `pending_dnb_investigation`
        set to None raises an error.
        """
        with pytest.raises(IntegrityError):
            CompanyFactory(pending_dnb_investigation=None)


class TestDNBInvestigationData:
    """
    Test `dnb_investigation_data`.
    """

    @pytest.mark.parametrize(
        'override',
        (
            {},
            {'dnb_investigation_data': None},
        ),
    )
    def test_null(self, override):
        """
        Test that dnb_investigation_data is nullable.
        """
        company = CompanyFactory(**override)
        db_company = Company.objects.get(id=company.id)
        assert db_company.dnb_investigation_data is None

    @pytest.mark.parametrize(
        'investigation_data',
        (
            {},
            {'foo': 'bar'},
        ),
    )
    def test_value(self, investigation_data):
        """
        Test that dnb_investigation_data can be set.
        """
        company = CompanyFactory(dnb_investigation_data=investigation_data)
        db_company = Company.objects.get(id=company.id)
        assert db_company.dnb_investigation_data == investigation_data


@pytest.mark.parametrize(
    'duns_number,global_ultimate_duns_number,expected_is_global_ultimate',
    (
        ('', '', False),
        (None, '', False),
        ('123456789', '123456789', True),
        ('999999999', '123456789', False),
    ),
)
def test_is_global_ultimate(duns_number, global_ultimate_duns_number, expected_is_global_ultimate):
    """
    Test that the `Company.is_global_ultimate` property returns the correct response
    for a variety of scenarios.
    """
    company = CompanyFactory(
        duns_number=duns_number,
        global_ultimate_duns_number=global_ultimate_duns_number,
    )
    assert company.is_global_ultimate == expected_is_global_ultimate

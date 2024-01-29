from unittest.mock import Mock
import pytest

from django.db.utils import IntegrityError

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory, AdviserFactory
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


class TestOneListAccountOwner():
    """
    Test schedule_sync_investment_projects_of_subsidiary_companies is only called when
    one_list_account_owner has changed.
    """

    def test_one_list_account_owner_changed(self, monkeypatch):
        one_list_account_owner = AdviserFactory()
        company = CompanyFactory()

        mock_schedule_sync_investment_projects_of_subsidiary_companies = Mock()
        monkeypatch.setattr(
            'datahub.search.company.tasks.' +
            'schedule_sync_investment_projects_of_subsidiary_companies',
            mock_schedule_sync_investment_projects_of_subsidiary_companies,
        )

        # Mock call to schedule_sync_investment_projects_of_subsidiary_companies
        company.one_list_account_owner = one_list_account_owner
        company.save()
        mock_schedule_sync_investment_projects_of_subsidiary_companies.assert_called_once_with(
            company,
        )

    def test_one_list_account_owner_not_changed(self, monkeypatch):
        company = CompanyFactory()

        mock_schedule_sync_investment_projects_of_subsidiary_companies = Mock()
        monkeypatch.setattr(
            ('datahub.search.company.tasks.' +
                'schedule_sync_investment_projects_of_subsidiary_companies'),
            mock_schedule_sync_investment_projects_of_subsidiary_companies,
        )

        company.save()
        mock_schedule_sync_investment_projects_of_subsidiary_companies.assert_not_called()

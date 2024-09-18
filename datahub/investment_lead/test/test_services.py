import pytest

from datahub.company.models.company import Company
from datahub.company.test.factories import CompanyFactory
from datahub.investment_lead.services import match_by_duns_number, process_eyb_lead
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.investment_lead.test.utils import assert_company_matches_eyb_lead


@pytest.mark.django_db
class TestEYBLeadServices:
    """Tests EYB Lead services"""

    def test_duns_number_matches_existing_company(self):
        company = CompanyFactory(duns_number='123456789')
        eyb_lead = EYBLeadFactory(duns_number='123456789')

        found, found_company = match_by_duns_number(eyb_lead.duns_number)

        assert found is True
        assert found_company.id == company.id

    def test_duns_number_does_not_match_company(self):
        CompanyFactory(duns_number='123456789')
        eyb_lead = EYBLeadFactory(duns_number='123456788')

        found, found_company = match_by_duns_number(eyb_lead.duns_number)

        assert found is False
        assert found_company is None

    def test_add_new_company_from_eyb_lead(self):
        eyb_lead = EYBLeadFactory(duns_number=None)

        process_eyb_lead(eyb_lead)

        company = Company.objects.all().order_by('modified_on').last()

        assert_company_matches_eyb_lead(eyb_lead, company)

import pytest

from django.db import IntegrityError

from datahub.company.models.company import Company
from datahub.company.test.factories import CompanyFactory
from datahub.investment_lead.services import match_by_duns_number, add_new_company_from_eyb_lead, process_eyb_lead
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.investment_lead.test.utils import assert_eyb_lead_matches_company


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

    def test_attach_existing_company_from_eyb_lead(self):
        company = CompanyFactory(duns_number='123456789')
        eyb_lead = EYBLeadFactory(duns_number='123456789')

        process_eyb_lead(eyb_lead)

        assert eyb_lead.company is not None
        assert eyb_lead.company == company

    def test_add_new_company_from_eyb_lead(self):
        eyb_lead = EYBLeadFactory(duns_number=None)

        company = add_new_company_from_eyb_lead(eyb_lead)

        company = Company.objects.get(pk=company.pk)
        assert_eyb_lead_matches_company(company, eyb_lead)

        assert eyb_lead.company == company

    def test_add_new_company_with_company_name_none_fails(self):
        eyb_lead = EYBLeadFactory(duns_number=None)
        eyb_lead.company_name = None

        with pytest.raises(IntegrityError):
            add_new_company_from_eyb_lead(eyb_lead)

    def test_add_new_company_without_address_country_none_fails(self):
        eyb_lead = EYBLeadFactory(duns_number=None)
        eyb_lead.address_county = None

        with pytest.raises(IntegrityError):
            add_new_company_from_eyb_lead(eyb_lead)

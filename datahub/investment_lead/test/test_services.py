import pytest

from datahub.company.models.company import Company
from datahub.investment_lead.services import process_eyb_lead
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.investment_lead.test.utils import assert_company_matches_eyb_lead


@pytest.mark.django_db
class TestEYBLeadServices:
    """Tests EYB Lead services"""

    def test_add_new_company_from_eyb_lead(self):
        eyb_lead = EYBLeadFactory(duns_number=None)

        process_eyb_lead(eyb_lead)

        company = Company.objects.all().order_by('modified_on').last()

        assert_company_matches_eyb_lead(eyb_lead, company)

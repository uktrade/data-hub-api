import pytest
import pytz

from datahub.company_activity.models import CompanyActivity
from datahub.investment_lead.test.factories import EYBLeadFactory


@pytest.mark.django_db
class TestEYBLead:
    """Tests EYB Lead model"""

    def test_save_without_company_no_company_activity(self):
        assert not CompanyActivity.objects.all().exists()
        EYBLeadFactory(company=None)
        assert not CompanyActivity.objects.all().exists()

    def test_save_with_company_creates_company_activity(self):
        assert not CompanyActivity.objects.all().exists()

        eyb_lead = EYBLeadFactory()

        assert CompanyActivity.objects.all().count() == 1

        company_activity = CompanyActivity.objects.get(eyb_lead=eyb_lead.id)
        assert company_activity.company_id == eyb_lead.company.id
        assert company_activity.date == eyb_lead.triage_created.replace(tzinfo=pytz.UTC)
        assert company_activity.activity_source == CompanyActivity.ActivitySource.eyb_lead

    def test_str(self, eyb_lead_instance_from_db):
        """Test the human friendly string representation of the object"""
        assert str(eyb_lead_instance_from_db) == eyb_lead_instance_from_db.name

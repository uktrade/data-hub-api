import pytest

from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.utils import verify_eyb_lead_data


@pytest.mark.django_db
class TestEYBLead:
    """Tests EYB Lead model"""

    def test_db_instance_matches_factory_instance(self, eyb_lead_data, eyb_lead_db):
        assert EYBLead.objects.all().exists()
        verify_eyb_lead_data(eyb_lead_db, eyb_lead_data)

    def test_str(self, eyb_lead_db):
        """Test the human friendly string representation of the object"""
        hashed_id = f'{eyb_lead_db.triage_hashed_uuid}'
        assert str(eyb_lead_db) == hashed_id

    def test_triage_uuid_and_user_uuid_match(self, eyb_lead_db):
        # TODO: verify whether this will be needed in the long run
        # we might squash the *_uuids into one
        assert eyb_lead_db.triage_hashed_uuid == eyb_lead_db.user_hashed_uuid

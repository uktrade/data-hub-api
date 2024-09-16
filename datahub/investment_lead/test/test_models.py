import pytest

from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.utils import verify_eyb_lead_data


@pytest.mark.django_db
class TestEYBLead:
    """Tests EYB Lead model"""

    def test_db_instance_matches_factory_instance(
        self, eyb_lead_factory_data, eyb_lead_instance_from_db,
    ):
        assert EYBLead.objects.all().exists()
        verify_eyb_lead_data(
            eyb_lead_instance_from_db, eyb_lead_factory_data, data_type='factory',
        )

    def test_str(self, eyb_lead_instance_from_db):
        """Test the human friendly string representation of the object"""
        assert str(eyb_lead_instance_from_db) == eyb_lead_instance_from_db.name

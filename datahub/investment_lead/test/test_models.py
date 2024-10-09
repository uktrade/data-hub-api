import pytest


@pytest.mark.django_db
class TestEYBLead:
    """Tests EYB Lead model"""

    def test_str(self, eyb_lead_instance_from_db):
        """Test the human friendly string representation of the object"""
        assert str(eyb_lead_instance_from_db) == eyb_lead_instance_from_db.name

import pytest

from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import EYBLeadSerializer
from datahub.investment_lead.test.utils import verify_eyb_lead_data


@pytest.mark.django_db
@pytest.mark.usefixtures('eyb_lead_data', 'eyb_lead_d')
class TestEYBLeadSerializer:
    """Tests for EYBLeadSerializer."""

    def test_eyb_lead_serializer(self, eyb_lead_data, eyb_lead_db):
        eyb_object = EYBLead.objects.first()
        eyb_object_serialized = EYBLeadSerializer(eyb_object)

        verify_eyb_lead_data(eyb_object, eyb_object_serialized.data)

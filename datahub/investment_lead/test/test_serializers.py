import pytest

from rest_framework import serializers

from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import (
    EYBLeadSerializer,
    UUIDS_ERROR_MESSAGE,
)
from datahub.investment_lead.test.utils import verify_eyb_lead_data


@pytest.mark.django_db
@pytest.mark.usefixtures('eyb_lead_data', 'eyb_lead_db')
class TestEYBLeadSerializer:
    """Tests for EYBLeadSerializer."""

    def test_eyb_lead_serializer_raises_if_uuids_different(self, eyb_lead_data, eyb_lead_db):
        invalid_eyb_data = eyb_lead_data.copy()
        invalid_eyb_data['triage_hashed_uuid'] = '123abc'
        invalid_eyb_data['user_hashed_uuid'] = '456def'
        eyb_serializer = EYBLeadSerializer(data=invalid_eyb_data)

        with pytest.raises(serializers.ValidationError) as serial_error:
            eyb_serializer.is_valid(raise_exception=True)

        # Can this be done more elegantly?
        error_message = str(serial_error.value.detail['non_field_errors'][0])
        assert error_message == UUIDS_ERROR_MESSAGE

    def test_eyb_lead_serializer_as_expected(self, eyb_lead_data, eyb_lead_db):
        eyb_object = EYBLead.objects.first()
        eyb_object_serialized = EYBLeadSerializer(eyb_object)

        verify_eyb_lead_data(eyb_object, eyb_object_serialized.data)

import pytest

from rest_framework import serializers

from datahub.investment_lead.serializers import (
    EYBLeadSerializer,
    UUIDS_ERROR_MESSAGE,
)
from datahub.investment_lead.test.utils import verify_eyb_lead_data


@pytest.mark.django_db
@pytest.mark.usefixtures('eyb_lead_data', 'eyb_lead_db')
class TestEYBLeadSerializer:
    """Tests for EYBLeadSerializer."""

    def test_eyb_lead_serializer_raises_if_uuids_different(self, eyb_lead_data):
        invalid_eyb_data = eyb_lead_data.copy()
        invalid_eyb_data['triage_hashed_uuid'] = '123abc'
        invalid_eyb_data['user_hashed_uuid'] = '456def'
        eyb_serializer = EYBLeadSerializer(data=invalid_eyb_data)

        with pytest.raises(serializers.ValidationError):
            eyb_serializer.is_valid(raise_exception=True)

        assert UUIDS_ERROR_MESSAGE in eyb_serializer.errors['non_field_errors']

    def test_eyb_lead_serializer_as_expected(self, eyb_lead_db):
        db_instance = eyb_lead_db
        serialized_instance = EYBLeadSerializer(eyb_lead_db)
        verify_eyb_lead_data(db_instance, serialized_instance.data)

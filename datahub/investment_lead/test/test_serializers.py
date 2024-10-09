import pytest

from datahub.core import constants
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import (
    CreateEYBLeadTriageSerializer,
    CreateEYBLeadUserSerializer,
    RetrieveEYBLeadSerializer,
)
from datahub.investment_lead.test.conftest import get_segments_from_sector_instance
from datahub.investment_lead.test.utils import (
    assert_ingested_eyb_triage_data,
    assert_ingested_eyb_user_data,
    assert_retrieved_eyb_lead_data,
)
from datahub.metadata.models import (
    Country,
    Sector,
    UKRegion,
)

pytestmark = pytest.mark.django_db


class TestCreateEYBLeadTriageSerializer:
    """Tests for CreateEYBLeadTriageSerializer"""

    def test_create_lead_from_valid_triage_data(self, eyb_lead_triage_data):
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_triage_data(instance, serializer.data)

    def test_create_lead_from_invalid_triage_data(self, eyb_lead_triage_data):
        """Tests invalid choice-field and related-field data raises validation errors."""
        eyb_lead_triage_data.update({
            # 'sector': 'Invalid sector name',
            'location': 'Invalid location name',
            'hiring': 'Invalid hiring choice',
            'spend': 'Invalid spend choice',
        })
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert not serializer.is_valid()
        # assert 'sector' in serializer.errors
        assert 'location' in serializer.errors
        assert 'hiring' in serializer.errors
        assert 'spend' in serializer.errors

    def test_create_lead_from_incomplete_triage_data(self, eyb_lead_triage_data):
        eyb_lead_triage_data.pop('sector')
        eyb_lead_triage_data.pop('intent')
        eyb_lead_triage_data.pop('location')
        eyb_lead_triage_data.pop('hiring')
        eyb_lead_triage_data.pop('spend')
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert not serializer.is_valid()
        assert 'sector' in serializer.errors
        assert 'intent' in serializer.errors
        assert 'location' in serializer.errors
        assert 'hiring' in serializer.errors
        assert 'spend' in serializer.errors

    def test_related_field_conversion(self, eyb_lead_triage_data):
        mining_sector = Sector.objects.get(
            pk=constants.Sector.mining_mining_vehicles_transport_equipment.value.id,
        )
        wales_region = UKRegion.objects.get(
            pk=constants.UKRegion.wales.value.id,
        )
        level_zero_segment, level_one_segment, level_two_segment = \
            get_segments_from_sector_instance(mining_sector)
        eyb_lead_triage_data.update({
            'sector': level_zero_segment,
            'sectorSub': level_one_segment,
            'sectorSubSub': level_two_segment,
            'location': wales_region.name,
        })
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert serializer.is_valid(), serializer.errors
        validated_data = serializer.validated_data
        assert validated_data['sector'].pk == mining_sector.pk
        assert validated_data['location'].pk == wales_region.pk


class TestCreateEYBLeadUserSerializer:
    """Tests for CreateEYBLeadUserSerializer"""

    def test_create_lead_from_valid_user_data(self, eyb_lead_user_data):
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_user_data(instance, serializer.data)

    def test_create_lead_from_invalid_user_data(self, eyb_lead_user_data):
        """Tests invalid choice-field and related-field data raises validation errors."""
        eyb_lead_user_data.update({
            'companyLocation': 'Invalid country name',
            'landingTimeframe': 'Invalid landing timeframe choice',
        })
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert not serializer.is_valid()
        # assert 'companyLocation' in serializer.errors
        assert 'landingTimeframe' in serializer.errors

    def test_create_lead_from_incomplete_user_data(self, eyb_lead_user_data):
        eyb_lead_user_data.pop('companyLocation')
        eyb_lead_user_data.pop('landingTimeframe')
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert not serializer.is_valid()
        assert 'companyLocation' in serializer.errors
        assert 'landingTimeframe' in serializer.errors

    def test_related_field_conversion(self, eyb_lead_user_data):
        canada_country = Country.objects.get(
            pk=constants.Country.canada.value.id,
        )
        eyb_lead_user_data.update({
            'companyLocation': canada_country.iso_alpha2_code,
        })
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert serializer.is_valid(), serializer.errors
        validated_data = serializer.validated_data
        assert validated_data['address_country'].pk == canada_country.pk


class TestRetrieveEYBLeadSerializer:
    """Tests for RetrieveEYBLeadSerializer"""

    def test_retrieve_eyb_lead(self, eyb_lead_instance_from_db):
        serializer = RetrieveEYBLeadSerializer(eyb_lead_instance_from_db)
        assert_retrieved_eyb_lead_data(eyb_lead_instance_from_db, serializer.data)

    def test_serialize_queryset(self, eyb_lead_instance_from_db):
        queryset = EYBLead.objects.all()
        serializer = RetrieveEYBLeadSerializer(queryset, many=True)
        assert len(serializer.data) == 1
        assert_retrieved_eyb_lead_data(eyb_lead_instance_from_db, serializer.data[0])

import pytest

from datahub.core import constants
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import (
    CreateEYBLeadMarketingSerializer,
    CreateEYBLeadTriageSerializer,
    CreateEYBLeadUserSerializer,
    RetrieveEYBLeadSerializer,
)
from datahub.investment_lead.test.utils import (
    verify_eyb_lead_data,
    verify_eyb_marketing_data,
    verify_eyb_triage_data,
    verify_eyb_user_data,
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
        verify_eyb_triage_data(instance, serializer.validated_data, data_type='factory')

    def test_create_lead_from_invalid_triage_data(self, eyb_lead_triage_data):
        """Tests invalid choice-field and related-field data raises validation errors."""
        eyb_lead_triage_data.update({
            'sector': 'Invalid sector name',
            'location': 'Invalid location name',
            'hiring': 'Invalid hiring choice',
            'spend': 'Invalid spend choice',
        })
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert not serializer.is_valid()
        assert 'sector' in serializer.errors
        assert 'location' in serializer.errors
        assert 'hiring' in serializer.errors
        assert 'spend' in serializer.errors

    def test_create_lead_from_incomplete_triage_data(self, eyb_lead_triage_data):
        eyb_lead_triage_data.pop('sector')
        eyb_lead_triage_data.pop('location')
        eyb_lead_triage_data.pop('hiring')
        eyb_lead_triage_data.pop('spend')
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert not serializer.is_valid()
        assert 'sector' in serializer.errors
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
        eyb_lead_triage_data.update({
            'sector': mining_sector.segment,
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
        verify_eyb_user_data(instance, serializer.validated_data, data_type='factory')

    def test_create_lead_from_invalid_user_data(self, eyb_lead_user_data):
        """Tests invalid choice-field and related-field data raises validation errors."""
        eyb_lead_user_data.update({
            'address_country': 'Invalid country name',
            'landing_timeframe': 'Invalid landing timeframe choice',
        })
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert not serializer.is_valid()
        assert 'address_country' in serializer.errors
        assert 'landing_timeframe' in serializer.errors

    def test_create_lead_from_incomplete_user_data(self, eyb_lead_user_data):
        eyb_lead_user_data.pop('address_country')
        eyb_lead_user_data.pop('landing_timeframe')
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert not serializer.is_valid()
        assert 'address_country' in serializer.errors
        assert 'landing_timeframe' in serializer.errors

    def test_related_field_conversion(self, eyb_lead_user_data):
        canada_country = Country.objects.get(
            pk=constants.Country.canada.value.id,
        )
        eyb_lead_user_data.update({
            'address_country': canada_country.iso_alpha2_code,
        })
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert serializer.is_valid(), serializer.errors
        validated_data = serializer.validated_data
        assert validated_data['address_country'].pk == canada_country.pk


class TestCreateEYBLeadMarketingSerializer:
    """Tests for CreateEYBLeadMarketingSerializer"""

    def test_create_lead_from_valid_marketing_data(self, eyb_lead_marketing_data):
        serializer = CreateEYBLeadMarketingSerializer(data=eyb_lead_marketing_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        verify_eyb_marketing_data(instance, serializer.validated_data)

    def test_create_lead_from_invalid_marketing_data(self, eyb_lead_marketing_data):
        """Tests empty marketing data raises validation errors."""
        eyb_lead_marketing_data.update({
            'utm_name': None,
            'utm_source': None,
            'utm_medium': None,
            'utm_content': None,
        })
        serializer = CreateEYBLeadMarketingSerializer(data=eyb_lead_marketing_data)
        assert not serializer.is_valid()
        assert 'utm_name' in serializer.errors
        assert 'utm_source' in serializer.errors
        assert 'utm_medium' in serializer.errors
        assert 'utm_content' in serializer.errors

    def test_create_lead_from_incomplete_marketing_data(self, eyb_lead_marketing_data):
        eyb_lead_marketing_data.pop('utm_name')
        eyb_lead_marketing_data.pop('utm_source')
        eyb_lead_marketing_data.pop('utm_medium')
        eyb_lead_marketing_data.pop('utm_content')
        serializer = CreateEYBLeadMarketingSerializer(data=eyb_lead_marketing_data)
        assert not serializer.is_valid()
        assert 'utm_name' in serializer.errors
        assert 'utm_source' in serializer.errors
        assert 'utm_medium' in serializer.errors
        assert 'utm_content' in serializer.errors


class TestRetrieveEYBLeadSerializer:
    """Tests for RetrieveEYBLeadSerializer"""

    def test_retrieve_eyb_lead(self, eyb_lead_instance_from_db):
        serializer = RetrieveEYBLeadSerializer(eyb_lead_instance_from_db)
        verify_eyb_lead_data(eyb_lead_instance_from_db, serializer.data, data_type='nested')

    def test_serialize_queryset(self, eyb_lead_instance_from_db):
        queryset = EYBLead.objects.all()
        serializer = RetrieveEYBLeadSerializer(queryset, many=True)
        assert len(serializer.data) == 1
        verify_eyb_lead_data(eyb_lead_instance_from_db, serializer.data[0], data_type='nested')

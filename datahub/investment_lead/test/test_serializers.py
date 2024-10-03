import pytest

from datahub.core import constants
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import (
    CreateEYBLeadSerializer,
    RetrieveEYBLeadSerializer,
    UUIDS_ERROR_MESSAGE,
)
from datahub.investment_lead.test.utils import verify_eyb_lead_data
from datahub.metadata.models import (
    Country,
    Sector,
    UKRegion,
)

pytestmark = pytest.mark.django_db


class TestBaseEYBLeadSerializer:
    """Tests for BaseEYBLeadSerializer"""

    def test_eyb_lead_serializer_raises_if_uuids_different(self, eyb_lead_post_data):
        eyb_lead_post_data['triage_hashed_uuid'] = '123abc'
        eyb_lead_post_data['user_hashed_uuid'] = '456def'
        serializer = CreateEYBLeadSerializer(data=eyb_lead_post_data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert serializer.errors['non_field_errors'] == [UUIDS_ERROR_MESSAGE]


class TestCreateEYBLeadSerializer:
    """Tests for CreateEYBLeadSerializer"""

    def test_create_valid_eyb_lead(self, eyb_lead_post_data):
        serializer = CreateEYBLeadSerializer(data=eyb_lead_post_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        verify_eyb_lead_data(instance, serializer.validated_data, data_type='factory')

    def test_create_invalid_eyb_lead(self, eyb_lead_post_data):
        eyb_lead_post_data['spend'] = 'Invalid spend choice'
        serializer = CreateEYBLeadSerializer(data=eyb_lead_post_data)
        assert not serializer.is_valid()
        assert 'spend' in serializer.errors

    def test_related_field_validation(self, eyb_lead_post_data):
        eyb_lead_post_data.update({
            'sector': 'Invalid sector name',
            'location': 'Invalid UK region name',
            'address_country': 'Invalid country ISO code',
        })
        serializer = CreateEYBLeadSerializer(data=eyb_lead_post_data)
        assert not serializer.is_valid()
        assert 'sector' in serializer.errors
        assert 'location' in serializer.errors
        assert 'address_country' in serializer.errors

    def test_related_field_conversion(self, eyb_lead_post_data):
        mining_sector = Sector.objects.get(
            pk=constants.Sector.mining_mining_vehicles_transport_equipment.value.id,
        )
        wales_region = UKRegion.objects.get(
            pk=constants.UKRegion.wales.value.id,
        )
        canada_country = Country.objects.get(
            pk=constants.Country.canada.value.id,
        )
        eyb_lead_post_data.update({
            'sector': mining_sector.segment,
            'location': wales_region.name,
            'address_country': canada_country.iso_alpha2_code,
        })
        serializer = CreateEYBLeadSerializer(data=eyb_lead_post_data)
        assert serializer.is_valid(), serializer.errors
        validated_data = serializer.validated_data
        assert validated_data['sector'].pk == mining_sector.pk
        assert validated_data['location'].pk == wales_region.pk
        assert validated_data['address_country'].pk == canada_country.pk

    def test_create_without_utm_parameters(self, eyb_lead_post_data):
        eyb_lead_post_data.update({
            'utm_name': '',
            'utm_campaign': '',
            'utm_source': '',
            'utm_medium': '',
        })
        serializer = CreateEYBLeadSerializer(data=eyb_lead_post_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        verify_eyb_lead_data(instance, serializer.validated_data, data_type='factory')


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

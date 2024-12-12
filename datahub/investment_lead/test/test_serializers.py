from datetime import datetime

import pytest

from datahub.core import constants
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import (
    CreateEYBLeadMarketingSerializer,
    CreateEYBLeadTriageSerializer,
    CreateEYBLeadUserSerializer,
    RetrieveEYBLeadSerializer,
)
from datahub.investment_lead.test.factories import (
    eyb_lead_marketing_record_faker,
    generate_hashed_uuid,
)
from datahub.investment_lead.test.utils import (
    assert_ingested_eyb_marketing_data,
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

    def test_create_lead_from_partially_valid_triage_data(self):
        """Tests a lead is created with the minimum required fields."""
        partially_valid_data = {
            'hashedUuid': generate_hashed_uuid(),
            'created': datetime.today(),
            'modified': datetime.today(),
            'sector': 'Mining',
        }
        serializer = CreateEYBLeadTriageSerializer(data=partially_valid_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_triage_data(instance, serializer.data)

    def test_create_lead_from_incomplete_triage_data(self, eyb_lead_triage_data):
        """Tests missing required fields raises validation error."""
        required_fields = [
            'hashedUuid',
            'created',
            'modified',
            'sector',
        ]
        for key in required_fields:
            eyb_lead_triage_data.pop(key)
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert not serializer.is_valid()
        for key in required_fields:
            assert key in serializer.errors

    def test_related_field_conversion(self, eyb_lead_triage_data):
        mining_sector = Sector.objects.get(
            pk=constants.Sector.mining_mining_vehicles_transport_equipment.value.id,
        )
        wales_region = UKRegion.objects.get(
            pk=constants.UKRegion.wales.value.id,
        )
        level_zero_segment, level_one_segment, level_two_segment = \
            Sector.get_segments_from_sector_instance(mining_sector)
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
        assert validated_data['proposed_investment_region'].pk == wales_region.pk

    def test_create_lead_from_invalid_choice(self, eyb_lead_triage_data):
        """Tests invalid choice-field data raises validation errors."""
        eyb_lead_triage_data.update({
            'location': 'Invalid location name',
        })
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert not serializer.is_valid()
        assert 'location' in serializer.errors

    def test_create_lead_from_invalid_sector_data(self, eyb_lead_triage_data):
        """Tests invalid sector data raises validation errors."""
        level_one_segment = 'Invalid sector name'
        level_two_segment = 'Invalid sectorSub name'
        level_three_segment = None
        eyb_lead_triage_data.update({
            'sector': level_one_segment,
            'sectorSub': level_two_segment,
            'sectorSubSub': level_three_segment,
        })
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert not serializer.is_valid()
        sector_name = Sector.get_name_from_segments(
            [level_one_segment, level_two_segment, level_three_segment],
        )
        assert any(
            f'Sector "{sector_name}" does not exist.' in e
            for e in serializer.errors['non_field_errors']
        )

    @pytest.mark.parametrize(
        'value',
        [None, ''],
    )
    def test_required_fields_when_value_is_null_or_empty(self, value):
        """Tests null values and empty strings are handled correctly for required fields."""
        test_data = {
            'hashedUuid': value,
            'created': value,
            'modified': value,
            'sector': value,
        }
        serializer = CreateEYBLeadTriageSerializer(data=test_data)
        assert not serializer.is_valid()
        assert 'hashedUuid' in serializer.errors
        assert 'created' in serializer.errors
        assert 'modified' in serializer.errors
        assert 'sector' in serializer.errors

    @pytest.mark.parametrize(
        'value',
        [None, ''],
    )
    def test_non_required_fields_when_value_is_null_or_empty(self, eyb_lead_triage_data, value):
        """Tests null values and empty strings are handled correctly for non-required fields."""
        eyb_lead_triage_data.update({
            'sectorSub': value,
            'sectorSubSub': value,
            'intent': [value] if value == '' else value,
            'intentOther': value,
            'location': value,
            'locationCity': value,
            'locationNone': value,
            'hiring': value,
            'spend': value,
            'spendOther': value,
            'isHighValue': value,
        })
        serializer = CreateEYBLeadTriageSerializer(data=eyb_lead_triage_data)
        assert serializer.is_valid()
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_triage_data(instance, serializer.data)


class TestCreateEYBLeadUserSerializer:
    """Tests for CreateEYBLeadUserSerializer"""

    def test_create_lead_from_valid_user_data(self, eyb_lead_user_data):
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_user_data(instance, serializer.data)

    def test_create_lead_from_partially_valid_user_data(self, faker):
        """Tests a lead is created with the minimum required fields."""
        partially_valid_data = {
            'hashedUuid': generate_hashed_uuid(),
            'created': datetime.today(),
            'modified': datetime.today(),
            'companyName': faker.company(),
            'addressLine1': faker.street_address(),
            'town': faker.city(),
            'companyLocation': faker.country_code(),
            'fullName': faker.name(),
            'email': faker.email(),

        }
        serializer = CreateEYBLeadUserSerializer(data=partially_valid_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_user_data(instance, serializer.data)

    def test_create_lead_from_incomplete_user_data(self, eyb_lead_user_data):
        """Tests missing required fields raises validation error."""
        required_fields = [
            'hashedUuid',
            'created',
            'modified',
            'companyName',
            'addressLine1',
            'town',
            'companyLocation',
            'fullName',
            'email',
        ]
        for key in required_fields:
            eyb_lead_user_data.pop(key)
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert not serializer.is_valid()
        for key in required_fields:
            assert key in serializer.errors

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

    def test_create_lead_from_invalid_related_data(self, eyb_lead_user_data):
        """Tests invalid related-field data raises validation errors."""
        eyb_lead_user_data.update({
            'companyLocation': 'Invalid country name',
        })
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert not serializer.is_valid()
        assert 'companyLocation' in serializer.errors

    @pytest.mark.parametrize(
        'value',
        [None, ''],
    )
    def test_required_fields_when_value_is_null_or_empty(self, value):
        """Tests null values and empty strings are handled correctly for required fields."""
        test_data = {
            'hashedUuid': value,
            'created': value,
            'modified': value,
            'companyName': value,
            'addressLine1': value,
            'town': value,
            'companyLocation': value,
            'fullName': value,
            'email': value,
        }
        serializer = CreateEYBLeadUserSerializer(data=test_data)
        assert not serializer.is_valid()
        for field in test_data.keys():
            assert field in serializer.errors

    @pytest.mark.parametrize(
        'value',
        [None, ''],
    )
    def test_non_required_fields_when_value_is_null_or_empty(self, eyb_lead_user_data, value):
        """Tests null values and empty strings are handled correctly for non-required fields."""
        eyb_lead_user_data.update({
            'dunsNumber': value,
            'addressLine2': value,
            'county': value,
            'postcode': value,
            'companyWebsite': value,
            'role': value,
            'telephoneNumber': value,
            'agreeTerms': value,
            'agreeInfoEmail': value,
            'landingTimeframe': value,
        })
        serializer = CreateEYBLeadUserSerializer(data=eyb_lead_user_data)
        assert serializer.is_valid()
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_user_data(instance, serializer.data)


class TestCreateEYBLeadMarketingSerializer:
    """Tests for CreateEYBLeadMarketingSerializer"""

    def test_lead_is_created_when_all_fields_contain_valid_data(self, eyb_lead_marketing_data):
        serializer = CreateEYBLeadMarketingSerializer(data=eyb_lead_marketing_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_marketing_data(instance, serializer.data)

    def test_lead_is_created_when_only_required_fields_are_present(self, faker):
        """Tests a lead is created with the minimum required fields."""
        partially_valid_data = {
            'hashed_uuid': generate_hashed_uuid(),
        }
        serializer = CreateEYBLeadMarketingSerializer(data=partially_valid_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_marketing_data(instance, serializer.data)

    def test_missing_required_marketing_fields_raises_validation_error(
            self, eyb_lead_marketing_data):
        """Tests missing required fields raises validation error."""
        required_fields = [
            'hashed_uuid',
        ]
        for key in required_fields:
            eyb_lead_marketing_data.pop(key)
        serializer = CreateEYBLeadMarketingSerializer(data=eyb_lead_marketing_data)
        assert not serializer.is_valid()
        for key in required_fields:
            assert key in serializer.errors

    @pytest.mark.parametrize(
        'value',
        [None, ''],
    )
    def test_required_fields_with_null_or_empty_values_are_handled_correctly(self, value):
        """Tests null values and empty strings are handled correctly for required fields."""
        test_data = {
            'hashed_uuid': value,
        }
        serializer = CreateEYBLeadMarketingSerializer(data=test_data)
        assert not serializer.is_valid()
        for field in test_data.keys():
            assert field in serializer.errors

    @pytest.mark.parametrize(
        'value',
        [None, ''],
    )
    def test_non_required_fields_with_null_or_empty_values_are_handled_correctly(
        self, value,
    ):
        """Tests null values and empty strings are handled correctly for non-required fields."""
        marketing_data = eyb_lead_marketing_record_faker({
            'name': value,
            'medium': value,
            'source': value,
            'content': value,
        })
        serializer = CreateEYBLeadMarketingSerializer(data=marketing_data)
        assert serializer.is_valid()
        instance = serializer.save()
        assert isinstance(instance, EYBLead)
        assert EYBLead.objects.count() == 1
        assert_ingested_eyb_marketing_data(instance, serializer.data)


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

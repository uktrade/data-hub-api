import uuid

import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.investment_lead.test.utils import verify_eyb_lead_data
from datahub.metadata.models import Sector


EYB_LEAD_COLLECTION_URL = reverse('api-v4:investment-lead:eyb-lead-collection')


def eyb_lead_item_url(pk: uuid.uuid4) -> str:
    return reverse('api-v4:investment-lead:eyb-lead-item', kwargs={'pk': pk})


class TestEYBLeadCreateAPI(APITestMixin):
    """Test for create/update EYB lead view (via POST request)"""

    @pytest.mark.parametrize('method', ('delete', 'patch', 'get', 'put'))
    def test_methods_not_allowed(self, data_flow_api_client, method):
        """Tests that requests using unsupported methods are not allowed."""
        response = data_flow_api_client.request(method, EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_eyb_lead_list(self, data_flow_api_client, eyb_lead_post_data):
        """Tests that a list of leads are processed in a single request/response cycle."""
        response = data_flow_api_client.post(EYB_LEAD_COLLECTION_URL, json_=[eyb_lead_post_data])
        assert response.status_code == status.HTTP_201_CREATED
        assert 'created' in response.data

        created_lead = response.data['created'][0]
        assert EYBLead.objects.count() == 1
        instance = EYBLead.objects.get(
            triage_hashed_uuid=created_lead['triage_hashed_uuid'],
            user_hashed_uuid=created_lead['user_hashed_uuid'],
        )
        verify_eyb_lead_data(instance, eyb_lead_post_data, data_type='post')

    def test_create_empty_list(self, data_flow_api_client):
        """Tests that no leads are created if an empty list is POSTed."""
        response = data_flow_api_client.post(EYB_LEAD_COLLECTION_URL, json_=[])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'Expected a list of leads.'

    def test_create_invalid_list(self, data_flow_api_client, eyb_lead_post_data):
        """Tests that no leads are created if a list containing invalid data is POSTed."""
        invalid_post_data = eyb_lead_post_data.copy()
        invalid_post_data['sector'] = None
        response = data_flow_api_client.post(EYB_LEAD_COLLECTION_URL, json_=[invalid_post_data])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data

    def test_updating_existing_lead(self, data_flow_api_client, eyb_lead_post_data):
        """Tests that an existing lead is updated and does not create a duplicate."""
        existing_lead = EYBLeadFactory(
            triage_hashed_uuid=eyb_lead_post_data['triage_hashed_uuid'],
            user_hashed_uuid=eyb_lead_post_data['user_hashed_uuid'],
            location_id=constants.UKRegion.wales.value.id,
        )
        assert EYBLead.objects.count() == 1
        assert existing_lead.location.name == constants.UKRegion.wales.value.name

        modified_post_data = eyb_lead_post_data.copy()
        modified_post_data['location'] = constants.UKRegion.south_west.value.name
        response = data_flow_api_client.post(EYB_LEAD_COLLECTION_URL, json_=[modified_post_data])
        assert response.status_code == status.HTTP_201_CREATED
        assert 'updated' in response.data

        updated_lead = response.data['updated'][0]
        assert EYBLead.objects.count() == 1
        instance = EYBLead.objects.get(
            triage_hashed_uuid=updated_lead['triage_hashed_uuid'],
            user_hashed_uuid=updated_lead['user_hashed_uuid'],
        )
        assert instance.triage_hashed_uuid == eyb_lead_post_data['triage_hashed_uuid']
        assert instance.user_hashed_uuid == eyb_lead_post_data['user_hashed_uuid']
        assert instance.location.name == constants.UKRegion.south_west.value.name

    def test_creating_lead_with_sso_auth(
        self, test_user_with_view_permissions, eyb_lead_post_data,
    ):
        """Tests that the create endpoint doesn't allow SSO authentication"""
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.post(EYB_LEAD_COLLECTION_URL, json_=[eyb_lead_post_data])
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestEYBLeadRetrieveAPI(APITestMixin):
    """Tests for retrieve EYB lead view (via GET request)"""

    def test_retrieve_eyb_lead(self, test_user_with_view_permissions, eyb_lead_instance_from_db):
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        url = eyb_lead_item_url(eyb_lead_instance_from_db.pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        verify_eyb_lead_data(eyb_lead_instance_from_db, response.data, data_type='nested')

    def test_retrieve_non_existent_lead(self, test_user_with_view_permissions):
        non_existent_pk = uuid.uuid4()
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        url = eyb_lead_item_url(non_existent_pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_with_hawk_credentials(self, eyb_lead_instance_from_db, data_flow_api_client):
        """Tests that the retrieve endpoint doesn't allow hawk authentication"""
        url = eyb_lead_item_url(eyb_lead_instance_from_db.pk)
        response = data_flow_api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestEYBLeadListAPI(APITestMixin):
    """Tests for list EYB lead view (via GET request)"""

    def test_list_eyb_leads(self, test_user_with_view_permissions, eyb_lead_instance_from_db):
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        verify_eyb_lead_data(
            eyb_lead_instance_from_db, response.data['results'][0], data_type='nested',
        )

    def test_list_no_eyb_leads(self, test_user_with_view_permissions):
        """Tests that an empty list is returned if there are no EYB leads"""
        EYBLead.objects.all().delete()
        assert EYBLead.objects.count() == 0
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []

    def test_list_with_hawk_credentials(self, data_flow_api_client):
        """Tests that the list endpoint doesn't allow hawk authentication"""
        response = data_flow_api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_pagination(self, test_user_with_view_permissions):
        """Test that LimitOffsetPagination is enabled for this view"""
        number_of_leads = 3
        pagination_limit = 2
        EYBLeadFactory.create_batch(number_of_leads)
        assert EYBLead.objects.count() == number_of_leads
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'limit': pagination_limit})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == number_of_leads
        assert response.data['next'] is not None
        assert len(response.data['results']) == pagination_limit

    def test_filter_by_company_name(self, test_user_with_view_permissions):
        """Test filtering EYB leads by company name"""
        company_name = 'Mars Exports Ltd'
        company = CompanyFactory(name=company_name)
        EYBLeadFactory(company=company)
        EYBLeadFactory()
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'company': company_name})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['company']['name'] == company_name

    def test_filter_by_ancestor_sector(self, test_user_with_view_permissions):
        """Test filtering by sector returns leads with sectors that have the ancestor sector."""
        level_zero_sector = Sector.objects.get(pk=constants.Sector.mining.value.id)
        child_sector = Sector.objects.get(
            pk=constants.Sector.mining_mining_vehicles_transport_equipment.value.id,
        )
        unrelated_sector = Sector.objects.get(pk=constants.Sector.renewable_energy_wind.value.id)
        EYBLeadFactory(sector=level_zero_sector)
        EYBLeadFactory(sector=child_sector)
        EYBLeadFactory(sector=unrelated_sector)

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'sector': level_zero_sector.pk})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        sector_ids_in_results = set([lead['sector']['id'] for lead in response.data['results']])
        assert {str(level_zero_sector.pk), str(child_sector.pk)} == sector_ids_in_results

    def test_filter_by_multiple_ancestor_sectors(self, test_user_with_view_permissions):
        """Test filtering by multiple sectors."""
        level_zero_sector = Sector.objects.get(pk=constants.Sector.mining.value.id)
        child_sector = Sector.objects.get(
            pk=constants.Sector.mining_mining_vehicles_transport_equipment.value.id,
        )
        other_level_zero_sector = Sector.objects.get(pk=constants.Sector.defence.value.id)
        other_child_sector = Sector.objects.get(pk=constants.Sector.defence_air.value.id)
        unrelated_sector = Sector.objects.get(pk=constants.Sector.renewable_energy_wind.value.id)
        EYBLeadFactory(sector=level_zero_sector)
        EYBLeadFactory(sector=child_sector)
        EYBLeadFactory(sector=other_level_zero_sector)
        EYBLeadFactory(sector=other_child_sector)
        EYBLeadFactory(sector=unrelated_sector)

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={
            'sector': [level_zero_sector.pk, other_level_zero_sector.pk],
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        sector_ids_in_results = set([lead['sector']['id'] for lead in response.data['results']])
        assert {
            str(level_zero_sector.pk),
            str(child_sector.pk),
            str(other_level_zero_sector.pk),
            str(other_child_sector.pk),
        } == sector_ids_in_results

    def test_filter_by_non_existing_sector(self, test_user_with_view_permissions):
        """Test filtering EYB leads by non existent sector is handled without error."""
        non_existent_sector_uuid = uuid.uuid4()
        sector = Sector.objects.get(pk=constants.Sector.renewable_energy_wind.value.id)
        EYBLeadFactory(sector=sector)

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

        response = api_client.get(
            EYB_LEAD_COLLECTION_URL, data={'sector': str(non_existent_sector_uuid)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_filter_by_is_high_value(self, test_user_with_view_permissions):
        """Test filtering EYB leads by is high value status"""
        EYBLeadFactory(is_high_value=True)
        EYBLeadFactory(is_high_value=False)
        EYBLeadFactory(is_high_value=False)
        api_client = self.create_api_client(user=test_user_with_view_permissions)

        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'value': 'high'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['is_high_value'] is True

    def test_filter_by_is_low_value(self, test_user_with_view_permissions):
        """Test filtering EYB leads by is low value status"""
        EYBLeadFactory(is_high_value=True)
        EYBLeadFactory(is_high_value=True)
        EYBLeadFactory(is_high_value=False)
        api_client = self.create_api_client(user=test_user_with_view_permissions)

        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'value': 'low'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['is_high_value'] is False

    def test_filter_by_is_high_and_low_value(self, test_user_with_view_permissions):
        """Test filtering EYB leads by multiple values"""
        EYBLeadFactory(is_high_value=True)
        EYBLeadFactory(is_high_value=True)
        EYBLeadFactory(is_high_value=False)
        api_client = self.create_api_client(user=test_user_with_view_permissions)

        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'value': ['high', 'low']})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_filter_by_invalid_value(self, test_user_with_view_permissions):
        """Test filtering EYB leads by an invalid value returns no leads"""
        EYBLeadFactory(is_high_value=True)
        EYBLeadFactory(is_high_value=True)
        EYBLeadFactory(is_high_value=False)
        api_client = self.create_api_client(user=test_user_with_view_permissions)

        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'value': 'invalid_value'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

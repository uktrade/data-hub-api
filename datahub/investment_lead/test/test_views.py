import uuid

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.investment_lead.test.utils import assert_retrieved_eyb_lead_data
from datahub.metadata.models import Country, Sector


EYB_LEAD_COLLECTION_URL = reverse('api-v4:investment-lead:eyb-lead-collection')


def eyb_lead_item_url(pk: uuid.uuid4) -> str:
    return reverse('api-v4:investment-lead:eyb-lead-item', kwargs={'pk': pk})


class TestEYBLeadRetrieveAPI(APITestMixin):
    """Tests for retrieve EYB lead view (via GET request)"""

    def test_retrieve_eyb_lead(self, test_user_with_view_permissions, eyb_lead_instance_from_db):
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        url = eyb_lead_item_url(eyb_lead_instance_from_db.pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert_retrieved_eyb_lead_data(eyb_lead_instance_from_db, response.data)

    def test_retrieve_non_existent_lead(self, test_user_with_view_permissions):
        non_existent_pk = uuid.uuid4()
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        url = eyb_lead_item_url(non_existent_pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEYBLeadListAPI(APITestMixin):
    """Tests for list EYB lead view (via GET request)"""

    def test_list_eyb_leads(self, test_user_with_view_permissions, eyb_lead_instance_from_db):
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert_retrieved_eyb_lead_data(
            eyb_lead_instance_from_db, response.data['results'][0])

    def test_list_no_eyb_leads(self, test_user_with_view_permissions):
        """Tests that an empty list is returned if there are no EYB leads"""
        EYBLead.objects.all().delete()
        assert EYBLead.objects.count() == 0
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []

    def test_list_leads_with_missing_triage_or_user_component(
        self, test_user_with_view_permissions,
    ):
        """Tests the list view only return leads with both triage and user hashed UUIDs."""
        lead_with_both = EYBLeadFactory()
        lead_without_triage = EYBLeadFactory(triage_hashed_uuid='')
        lead_without_user = EYBLeadFactory(user_hashed_uuid='')
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        result_ids = set([lead['id'] for lead in response.data['results']])
        assert str(lead_with_both.pk) in result_ids
        assert {str(lead_without_triage.pk), str(lead_without_user.pk)} not in result_ids

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
        """Test filtering EYB leads by the EYBLead.company_name field."""
        company_name = 'Mars Exports Ltd'
        EYBLeadFactory(company_name=company_name)
        EYBLeadFactory()
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'company': company_name})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['company_name'] == company_name

    def test_filter_by_related_company_name(self, test_user_with_view_permissions):
        """Test filtering EYB leads by the EYBLead.company.name field."""
        company_name = 'Mars Exports Ltd'
        company = CompanyFactory(name=company_name)
        EYBLeadFactory(company=company)
        EYBLeadFactory()
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'company': company_name})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['company']['name'] == company_name

    def test_filter_by_both_company_name_fields(self, test_user_with_view_permissions):
        """Test filtering EYB leads by the EYBLead.company_name and EYBLead.company.name field."""
        company_name = 'Mars Exports Ltd'
        company = CompanyFactory(name=company_name)
        EYBLeadFactory(company=company)
        EYBLeadFactory(company_name=company_name)
        EYBLeadFactory()
        assert EYBLead.objects.count() == 3
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'company': company_name})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

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

    def test_filter_by_country(self, test_user_with_view_permissions):
        """Test filtering EYB leads by one country."""
        default_country = Country.objects.get(pk=constants.Country.france.value.id)
        unrelated_country = Country.objects.get(pk=constants.Country.greece.value.id)
        EYBLeadFactory(address_country_id=default_country.id)
        EYBLeadFactory(address_country_id=unrelated_country.id)

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={'country': default_country.pk})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        country_ids_in_results = set(
            [lead['address']['country']['id'] for lead in response.data['results']],
        )
        assert {str(default_country.pk)} == country_ids_in_results

    def test_filter_by_multiple_countries(self, test_user_with_view_permissions):
        """Test filtering EYB leads by multiple countries."""
        france_country = Country.objects.get(pk=constants.Country.france.value.id)
        greece_country = Country.objects.get(pk=constants.Country.greece.value.id)
        canada_country = Country.objects.get(pk=constants.Country.canada.value.id)
        italy_country = Country.objects.get(pk=constants.Country.italy.value.id)
        japan_country = Country.objects.get(pk=constants.Country.japan.value.id)

        EYBLeadFactory(address_country_id=france_country.id)
        EYBLeadFactory(address_country_id=greece_country.id)
        EYBLeadFactory(address_country_id=canada_country.id)
        EYBLeadFactory(address_country_id=italy_country.id)
        EYBLeadFactory(address_country_id=japan_country.id)

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

        response = api_client.get(EYB_LEAD_COLLECTION_URL, data={
            'country': [france_country.pk, greece_country.pk],
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        country_ids_in_results = set(
            [lead['address']['country']['id'] for lead in response.data['results']],
        )
        assert {
            str(france_country.pk),
            str(greece_country.pk),
        } == country_ids_in_results

    def test_filter_by_non_existing_country(self, test_user_with_view_permissions):
        """Test filtering EYB leads by non existent country is handled without error."""
        non_existing_country_uuid = uuid.uuid4()
        country = Country.objects.get(pk=constants.Country.france.value.id)
        EYBLeadFactory(address_country_id=country.id)

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

        response = api_client.get(
            EYB_LEAD_COLLECTION_URL, data={'country': str(non_existing_country_uuid)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_list_eyb_leads_default_order(self, test_user_with_view_permissions):
        """Test the default ordering of EYB leads reflects descending created_on."""
        to_create = 2
        for _ in range(to_create):
            EYBLeadFactory()

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(EYB_LEAD_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == to_create

        newest_timestamp = response.data['results'][0]['created_on']
        oldest_timestamp = response.data['results'][1]['created_on']

        assert newest_timestamp > oldest_timestamp

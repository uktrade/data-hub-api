import uuid

import pytest

from django.utils.timezone import now
from faker import Faker
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models.export import CompanyExport
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
    ExportExperienceFactory,
    ExportFactory,
    ExportYearFactory,
)
from datahub.core.constants import Country, Sector
from datahub.core.test_utils import (
    APITestMixin,
    format_date_or_datetime,
)
from datahub.metadata.test.factories import CountryFactory, SectorFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestAddExport(APITestMixin):
    """Test the POST export endpoint"""

    def _generate_valid_json(self):
        """Generate a json object containing valid values for a company export"""
        company = CompanyFactory()
        owner = AdviserFactory()
        team_members = AdviserFactory.create_batch(3)
        contacts = ContactFactory.create_batch(4)
        country = Country.anguilla.value.id
        sector = Sector.aerospace_assembly_aircraft.value.id
        title = Faker().word()
        export_value = 24
        export_experience = ExportExperienceFactory()
        estimated_win_date = now()
        estimated_export_years = ExportYearFactory()

        return {
            'company': company.id,
            'owner': owner.id,
            'team_members': [advisor.id for advisor in team_members],
            'contacts': [contact.id for contact in contacts],
            'destination_country': country,
            'sector': sector,
            'title': title,
            'estimated_export_value_amount': export_value,
            'exporter_experience': export_experience.id,
            'estimated_win_date': estimated_win_date,
            'estimated_export_value_years': estimated_export_years.id,
            'export_potential': CompanyExport.ExportPotential.MEDIUM.value,
        }

    def test_missing_mandatory_fields_return_expected_error(self):
        """
        Test when mandatory fields are not provided these fields are included in the
        error response
        """
        url = reverse('api-v4:export:collection')

        response = self.api_client.post(
            url,
            data={},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company': ['This field is required.'],
            'owner': ['This field is required.'],
            'contacts': ['This field is required.'],
            'destination_country': ['This field is required.'],
            'sector': ['This field is required.'],
            'estimated_export_value_years': ['This field is required.'],
            'title': ['This field is required.'],
            'estimated_export_value_amount': ['This field is required.'],
            'estimated_win_date': ['This field is required.'],
            'export_potential': ['This field is required.'],
        }

    def test_too_many_team_members_return_expected_error(self):
        """
        Test when the number of team_members provided is above the maximum allowed, the response
        contains this error message
        """
        url = reverse('api-v4:export:collection')
        data = self._generate_valid_json()
        data['team_members'] = [advisor.id for advisor in AdviserFactory.create_batch(6)]

        response = self.api_client.post(
            url,
            data=data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()

        assert response_data['team_members'] == ['You can only add 5 team members']

    def test_post_success(self):
        """Test a POST request with correct arguments provides a success response"""
        url = reverse('api-v4:export:collection')

        response = self.api_client.post(
            url,
            data=self._generate_valid_json(),
        )

        response_json = response.json()

        assert response.status_code == status.HTTP_201_CREATED
        assert uuid.UUID(response_json['id'])


class TestGetExport(APITestMixin):
    """Test the GET export endpoint"""

    def test_get_unknown_export_returns_error(self):
        """Test a GET with an unknown export id returns a not found error"""
        ExportFactory.create_batch(3)
        url = reverse('api-v4:export:item', kwargs={'pk': uuid.uuid4()})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_success(self):
        """Test a GET request with a known export id provides a success response"""
        export = ExportFactory(
            contacts=ContactFactory.create_batch(3),
            team_members=AdviserFactory.create_batch(4),
        )

        url = reverse('api-v4:export:item', kwargs={'pk': export.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert response.json() == {
            'id': str(export.pk),
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company': {'id': str(export.company.id), 'name': export.company.name},
            'contacts': [
                {'id': str(contact.id), 'name': contact.name} for contact in export.contacts.all()
            ],
            'created_by': None,
            'created_on': format_date_or_datetime(export.created_on),
            'destination_country': {
                'id': str(export.destination_country.id),
                'name': export.destination_country.name,
            },
            'estimated_export_value_amount': str(export.estimated_export_value_amount),
            'estimated_export_value_years': {
                'id': str(export.estimated_export_value_years.id),
                'name': export.estimated_export_value_years.name,
            },
            'estimated_win_date': format_date_or_datetime(export.estimated_win_date),
            'export_potential': export.export_potential,
            'exporter_experience': {
                'id': str(export.exporter_experience.id),
                'name': export.exporter_experience.name,
            },
            'modified_by': None,
            'modified_on': format_date_or_datetime(export.modified_on),
            'notes': export.notes,
            'owner': {
                'id': str(export.owner.id),
                'name': export.owner.name,
            },
            'sector': {
                'id': str(export.sector.id),
                'name': export.sector.name,
            },
            'status': export.status,
            'team_members': [
                {'id': str(team_member.id), 'name': team_member.name}
                for team_member in export.team_members.all()
            ],
            'title': export.title,
        }


class TestListExport(APITestMixin):
    """Test the LIST export endpoint"""

    def _assert_export_list_success(self, export):
        url = reverse('api-v4:export:collection')

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 1
        assert response.json()['results'][0]['id'] == str(export.id)

    def test_list_export_request_user_not_owner_user_not_team_member_returns_empty_results(self):
        """Test a GET with an unknown export id returns a not found error"""
        ExportFactory(owner=AdviserFactory(), team_members=[AdviserFactory()])
        url = reverse('api-v4:export:collection')

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 0

    def test_list_export_request_user_not_owner_user_is_a_team_member_returns_success_with_results(
        self,
    ):
        """Test a GET with an unknown export id returns a not found error"""
        export = ExportFactory(
            owner=AdviserFactory(),
            team_members=[
                self.user,
                AdviserFactory(),
            ],
        )
        self._assert_export_list_success(export)

    def test_list_export_request_user_is_owner_user_not_a_team_member_returns_success_with_results(
        self,
    ):
        """Test a GET with an unknown export id returns a not found error"""
        export = ExportFactory(owner=self.user, team_members=[AdviserFactory()])
        self._assert_export_list_success(export)

    def test_get_export_request_user_is_owner_user_is_a_team_member_returns_success(self):
        """Test a GET with an unknown export id returns a not found error"""
        export = ExportFactory(owner=self.user, team_members=[self.user])
        self._assert_export_list_success(export)

    @pytest.mark.parametrize(
        'batch_size,offset,limit,expected_count',
        (
            (5, 0, 5, 5),
            (5, 3, 10, 2),
            (2, 2, 1, 0),
        ),
    )
    def test_list_request_user_is_owner_user_is_a_team_member_with_pagination_success(
        self,
        batch_size,
        offset,
        limit,
        expected_count,
    ):
        """
        Test a request with pagination criteria returns expected export results
        """
        ExportFactory.create_batch(batch_size, owner=self.user, team_members=[self.user])

        url = reverse('api-v4:export:collection')
        response = self.api_client.get(
            url,
            data={
                'limit': limit,
                'offset': offset,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == batch_size
        assert len(response.json()['results']) == expected_count


class TestPatchExport(APITestMixin):
    """Test the PATCH export endpoint"""

    def test_patch_unknown_export_returns_error(self):
        """Test a PATCH with an unknown export id returns a not found error"""
        ExportFactory.create_batch(3)
        url = reverse('api-v4:export:item', kwargs={'pk': uuid.uuid4()})

        response = self.api_client.patch(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_too_many_team_members_return_expected_error(self):
        """
        Test when the number of team_members provided is above the maximum allowed, the response
        contains this error message
        """
        export = ExportFactory()
        url = reverse('api-v4:export:item', kwargs={'pk': export.id})

        response = self.api_client.patch(
            url,
            data={'team_members': [advisor.id for advisor in AdviserFactory.create_batch(6)]},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_success(self):
        """
        Test a PATCH request with a known export id provides a success response
        """
        modified_date = now()
        with freeze_time(modified_date):
            export = ExportFactory()
            url = reverse('api-v4:export:item', kwargs={'pk': export.id})

            response = self.api_client.patch(url, data={'title': 'New title'})

            assert response.status_code == status.HTTP_200_OK

            assert response.json() == {
                'id': str(export.pk),
                'archived': False,
                'archived_by': None,
                'archived_on': None,
                'archived_reason': None,
                'company': {'id': str(export.company.id), 'name': export.company.name},
                'contacts': [
                    {'id': str(contact.id), 'name': contact.name}
                    for contact in export.contacts.all()
                ],
                'created_by': None,
                'created_on': format_date_or_datetime(export.created_on),
                'destination_country': {
                    'id': str(export.destination_country.id),
                    'name': export.destination_country.name,
                },
                'estimated_export_value_amount': str(export.estimated_export_value_amount),
                'estimated_export_value_years': {
                    'id': str(export.estimated_export_value_years.id),
                    'name': export.estimated_export_value_years.name,
                },
                'estimated_win_date': format_date_or_datetime(export.estimated_win_date),
                'export_potential': export.export_potential,
                'exporter_experience': {
                    'id': str(export.exporter_experience.id),
                    'name': export.exporter_experience.name,
                },
                'modified_by': str(self.user.id),
                'modified_on': format_date_or_datetime(modified_date),
                'notes': export.notes,
                'owner': {
                    'id': str(export.owner.id),
                    'name': export.owner.name,
                },
                'sector': {
                    'id': str(export.sector.id),
                    'name': export.sector.name,
                },
                'status': export.status,
                'team_members': [
                    {'id': str(team_member.id), 'name': team_member.name}
                    for team_member in export.team_members.all()
                ],
                'title': 'New title',
            }


class TestDeleteExport(APITestMixin):
    """Test the DELETE export endpoint"""

    def test_delete_unknown_export_returns_error(self):
        """Test a DELETE with an unknown export id returns a not found error"""
        ExportFactory.create_batch(3)
        url = reverse('api-v4:export:item', kwargs={'pk': uuid.uuid4()})

        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_success(self):
        """
        Test a DELETE request with a known export id provides a success response, and
        request with the same id returns the item archived
        """
        export = ExportFactory()
        url = reverse('api-v4:export:item', kwargs={'pk': export.id})

        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = self.api_client.get(url)
        assert response.json()['archived']


class TestExportFilters(APITestMixin):
    """Test the filters on the GET export endpoint"""

    def test_filtered_by_status(self):
        """List of exports filtered by status."""
        ExportFactory(
            status=CompanyExport.ExportStatus.ACTIVE,
            owner=self.user,
        )
        ExportFactory(
            status=CompanyExport.ExportStatus.INACTIVE,
            owner=self.user,
        )
        ExportFactory(
            status=CompanyExport.ExportStatus.WON,
            owner=self.user,
        )

        url = reverse('api-v4:export:collection')
        response = self.api_client.get(
            url,
            {
                'status': CompanyExport.ExportStatus.WON,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['status'] == CompanyExport.ExportStatus.WON

    def test_filtered_by_export_potential(self):
        """List of exports filtered by export potential."""
        ExportFactory(
            export_potential=CompanyExport.ExportPotential.HIGH,
            owner=self.user,
        )
        ExportFactory(
            export_potential=CompanyExport.ExportPotential.MEDIUM,
            owner=self.user,
        )
        ExportFactory(
            export_potential=CompanyExport.ExportPotential.LOW,
            owner=self.user,
        )

        url = reverse('api-v4:export:collection')
        response = self.api_client.get(
            url,
            {
                'export_potential': CompanyExport.ExportPotential.LOW,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['export_potential'] == CompanyExport.ExportPotential.LOW

    def test_filtered_by_export_sector(self):
        """List of exports filtered by sector."""
        sector1 = SectorFactory()
        sector2 = SectorFactory()
        sector3 = SectorFactory()

        ExportFactory(
            sector=sector1,
            owner=self.user,
        )
        ExportFactory(
            sector=sector2,
            owner=self.user,
        )
        ExportFactory(
            sector=sector3,
            owner=self.user,
        )

        url = reverse('api-v4:export:collection')
        response = self.api_client.get(
            url,
            {
                'sector': str(sector3.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['sector']['id'] == str(sector3.pk)

    def test_filtered_by_export_country(self):
        """List of exports filtered by country."""
        country1 = CountryFactory()
        country2 = CountryFactory()
        country3 = CountryFactory()

        ExportFactory(
            destination_country=country1,
            owner=self.user,
        )
        ExportFactory(
            destination_country=country2,
            owner=self.user,
        )
        ExportFactory(
            destination_country=country3,
            owner=self.user,
        )

        url = reverse('api-v4:export:collection')
        response = self.api_client.get(
            url,
            {
                'destination_country': str(country3.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['destination_country']['id'] == str(country3.pk)

    def test_filtered_by_export_team_members(self):
        """List of exports filtered by team members"""
        team_member_1 = AdviserFactory()
        team_member_2 = AdviserFactory()
        team_member_3 = AdviserFactory()

        ExportFactory(
            team_members=[
                team_member_1,
            ],
            owner=self.user,
        )

        ExportFactory(
            team_members=[
                team_member_2,
            ],
            owner=self.user,
        )

        ExportFactory(
            team_members=[
                team_member_3,
            ],
            owner=self.user,
        )

        url = reverse('api-v4:export:collection')
        response = self.api_client.get(
            url,
            {
                'team_members': team_member_1.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['count'] == 1
        assert response_data['results'][0]['team_members'][0]['id'] == str(team_member_1.id)

    def test_filtered_by_archived(self):
        """List of exports filtered by archive value"""
        archived = ExportFactory(
            archived=True,
            owner=self.user,
        )
        not_archived = ExportFactory(
            archived=False,
            owner=self.user,
        )

        url = reverse('api-v4:export:collection')
        archived_response = self.api_client.get(
            url,
            {
                'archived': True,
            },
        )
        assert archived_response.status_code == status.HTTP_200_OK
        response_data = archived_response.json()

        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(archived.id)

        not_archived_response = self.api_client.get(
            url,
            {
                'archived': False,
            },
        )
        assert not_archived_response.status_code == status.HTTP_200_OK
        response_data = not_archived_response.json()

        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(not_archived.id)


class TestExportSortBy(APITestMixin):
    """Test the sorting on the GET export endpoint"""

    @pytest.mark.parametrize(
        'data,results',
        (
            (  # sort by title ASC
                {'sortby': 'title'},
                ['Title A', 'Title B', 'Title C'],
            ),
            (  # sort by title DESC
                {'sortby': '-title'},
                ['Title C', 'Title B', 'Title A'],
            ),
            (  # sort by created_on ASC
                {'sortby': 'created_on'},
                ['Title C', 'Title A', 'Title B'],
            ),
            (  # sort by created_on DESC
                {'sortby': '-created_on'},
                ['Title B', 'Title A', 'Title C'],
            ),
        ),
    )
    def test_sort_by_export_title(self, data, results):
        """Test sort by title (ascending)"""
        ExportFactory(
            title='Title C',
            owner=self.user,
        )
        ExportFactory(
            title='Title A',
            owner=self.user,
        )
        ExportFactory(
            title='Title B',
            owner=self.user,
        )

        url = reverse('api-v4:export:collection')
        response = self.api_client.get(url, data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        assert [result['title'] for result in response_data['results']] == results

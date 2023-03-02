import uuid

import pytest

from django.utils.timezone import now
from faker import Faker
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models.export import CompanyExport
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
    ExportExperienceFactory,
    ExportYearFactory,
)
from datahub.core.constants import Country, Sector
from datahub.core.test_utils import (
    APITestMixin,
)

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
            'team_members': ['This field is required.'],
            'contacts': ['This field is required.'],
            'destination_country': ['This field is required.'],
            'sector': ['This field is required.'],
            'exporter_experience': ['This field is required.'],
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

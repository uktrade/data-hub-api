from rest_framework.reverse import reverse
from rest_framework import status

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InteractionDITParticipantFactory,
)


class TestCompanyActivityViewSetV4(APITestMixin):
    """Tests for the get CompanyActivityViewSetV4."""

    def test_endpoint__has_company_data(self):
        """Test activity endpoint returns company data for given company"""

        company = CompanyFactory()

        requester = create_test_user()
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['id'] == str(company.id)
        assert response_data['name'] == company.name
        assert response_data['trading_names'] == company.trading_names

    def test_endpoint__has_company_interactions(self):
        """Test activity endpoint returns interactions for given company"""
        company = CompanyFactory()
        interaction = CompanyInteractionFactory(company=company)
        CompanyInteractionFactory(company=company)

        requester = create_test_user()
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})

        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['activities']) == 2

        activtiy = [
            activity
            for activity in response_data['activities']
            if activity["id"] == str(interaction.id)
        ][0]

        assert activtiy["id"] == str(interaction.id)
        assert activtiy["subject"] == interaction.subject
        assert activtiy["kind"] == interaction.kind
        assert (
            activtiy["communication_channel"]["name"]
            == interaction.communication_channel.name
        )
        assert activtiy["communication_channel"]["id"] == str(
            interaction.communication_channel.id
        )
        assert activtiy["service"]["name"] == interaction.service.name
        assert activtiy["service"]["id"] == str(interaction.service.id)

        assert activtiy["dit_participants"][0]["adviser"]["id"] == str(
            interaction.dit_participants.all()[0].adviser.id
        )

    def test_endpoint__has_interactions_for_given_company_only(self):
        """Test activity endpoint returns interaction for given company only"""
        company = CompanyFactory()
        interaction = CompanyInteractionFactory(company=company)
        CompanyInteractionFactory()

        requester = create_test_user()
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['activities']) == 1

        assert response_data['activities'][0]['id'] == str(interaction.id)

    def test_endpoint__can_filter_activities_by_adviser_only(self):
        """Test activity endpoint returns interactions for given adviser and company only"""
        adviser = AdviserFactory()
        company = CompanyFactory()
        interaction = CompanyInteractionFactory(
            company=company,
            dit_participants=[InteractionDITParticipantFactory(adviser=adviser)],
        )
        CompanyInteractionFactory(company=company)

        requester = create_test_user()
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})

        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['activities']) == 2

        response = api_client.post(url, {'advisers': [str(adviser.id)]})
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['activities']) == 1

        assert response_data['activities'][0]['id'] == str(interaction.id)

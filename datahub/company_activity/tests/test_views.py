from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    CompanyReferralInteractionFactory,
    InteractionDITParticipantFactory,
)


class TestCompanyActivityViewSetV4(APITestMixin):
    """Tests for the get CompanyActivityViewSetV4."""

    def test_endpoint__has_company_data(self):
        """Test activity endpoint returns company data for given company"""
        company = CompanyFactory()

        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['id'] == str(company.id)
        assert response_data['name'] == company.name
        assert response_data['trading_names'] == company.trading_names

    def test_endpoint__has_company_interactions(self):
        """Test activity endpoint returns interactions for given company"""
        company = CompanyFactory()
        interaction = CompanyInteractionFactory(company=company, companies=[])
        CompanyInteractionFactory(company=company, companies=[])

        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = self.api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['activities']['results']) == 2

        activtiy = [
            activity
            for activity in response_data['activities']['results']
            if activity['id'] == str(interaction.id)
        ][0]

        assert activtiy['id'] == str(interaction.id)
        assert activtiy['subject'] == interaction.subject
        assert activtiy['kind'] == interaction.kind
        assert activtiy['activity_source'] == 'interaction'
        assert (
            activtiy['communication_channel']['name']
            == interaction.communication_channel.name
        )
        assert activtiy['communication_channel']['id'] == str(
            interaction.communication_channel.id,
        )
        assert activtiy['service']['name'] == interaction.service.name
        assert activtiy['service']['id'] == str(interaction.service.id)

        assert activtiy['dit_participants'][0]['adviser']['id'] == str(
            interaction.dit_participants.all()[0].adviser.id,
        )

    def test_endpoint__has_interactions_for_given_company_only(self):
        """Test activity endpoint returns interaction for given company only"""
        company = CompanyFactory()
        interaction = CompanyInteractionFactory(company=company, companies=[])
        CompanyInteractionFactory(companies=[])

        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = self.api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['activities']['results']) == 1

        assert response_data['activities']['results'][0]['id'] == str(interaction.id)

    def test_endpoint__can_filter_activities_by_adviser_only(self):
        """Test activity endpoint returns interactions for given adviser and company only"""
        adviser = AdviserFactory()
        company = CompanyFactory()
        interaction = CompanyInteractionFactory(
            company=company,
            dit_participants=[InteractionDITParticipantFactory(adviser=adviser)],
            companies=[],
        )
        CompanyInteractionFactory(company=company, companies=[])
        referral = CompanyReferralInteractionFactory(
            company=company,
            dit_participants=[InteractionDITParticipantFactory(adviser=adviser)],
            companies=[],
        )
        CompanyReferralInteractionFactory(company=company, companies=[])

        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})

        response = self.api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['activities']['results']) == 4

        response = self.api_client.post(url, {'advisers': [str(adviser.id)]})
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['activities']['results']) == 2

        returned_ids = [
            response.get('id') for response in response_data['activities']['results']
        ]
        assert str(interaction.id) in returned_ids
        assert str(referral.id) in returned_ids

    def test_endpoint__can_handle_incorrect_advisor_id_param(self):
        """Test activity endpoint can handle an advisor id param that isn't a valid uuid"""
        adviser = AdviserFactory()
        company = CompanyFactory()
        CompanyInteractionFactory(company=company, companies=[])

        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = self.api_client.post(
            url,
            {'advisers': [str(adviser.id), 'not-a-uuid']},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['advisers']['1'] == ['Must be a valid UUID.']

    def test_endpoint__returns_forbidden_for_unauthenticated_requests(self):
        """Test activity endpoint returns Forbidden for unauthenticated requests"""
        company = CompanyFactory()

        requester = create_test_user()
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_endpoint__date_filter(self):
        """Test activity endpoint returns response filtered by the date"""
        company = CompanyFactory()
        adviser = AdviserFactory()
        interaction_before = CompanyInteractionFactory(
            company=company,
            companies=[],
            dit_participants=[InteractionDITParticipantFactory(adviser=adviser)],
            date='2023-01-01',
        )
        referral_before = CompanyReferralInteractionFactory(
            company=company,
            companies=[],
            company_referral__completed_on='2023-01-01',
            dit_participants=[InteractionDITParticipantFactory(adviser=adviser)],
        )
        interaction_after = CompanyInteractionFactory(
            company=company,
            companies=[],
            dit_participants=[InteractionDITParticipantFactory(adviser=adviser)],
            date='2024-02-01',
        )
        interaction_between = CompanyInteractionFactory(
            company=company,
            companies=[],
            dit_participants=[InteractionDITParticipantFactory(adviser=adviser)],
            date='2023-08-08',
        )

        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})

        response = self.api_client.post(url)
        response_data = response.json()
        assert len(response_data['activities']['results']) == 4

        payload = {
            'date_after': '2024-01-01',
        }

        response = self.api_client.post(url, data=payload)
        response_data = response.json()
        assert len(response_data['activities']['results']) == 1
        assert response_data['activities']['results'][0]['id'] == str(
            interaction_after.id,
        )

        payload = {
            'date_before': '2024-01-01',
        }
        response = self.api_client.post(url, data=payload)
        response_data = response.json()
        assert len(response_data['activities']['results']) == 3
        returned_ids = [
            response.get('id') for response in response_data['activities']['results']
        ]
        assert str(interaction_before.id) in returned_ids
        assert str(interaction_between.id) in returned_ids
        assert str(referral_before.id) in returned_ids

        payload = {
            'date_before': '2023-12-30',
            'date_after': '2023-05-06',
        }

        response = self.api_client.post(url, data=payload)
        response_data = response.json()
        assert len(response_data['activities']['results']) == 1
        assert response_data['activities']['results'][0]['id'] == str(
            interaction_between.id,
        )

    def test_endpoint__invalid_date_filter(self):
        """Test activity endpoint handles invalid dates"""
        company = CompanyFactory()

        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        payload = {
            'date_after': 'abcd',
        }

        response = self.api_client.post(url, data=payload)
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['date_after'] == [
            'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.',
        ]

        payload = {
            'date_before': 'abcd',
        }

        response = self.api_client.post(url, data=payload)
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['date_before'] == [
            'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.',
        ]

    def test_endpoint__pagination(self):
        """Test activity endpoint returns response filtered by the date"""
        company = CompanyFactory()
        CompanyInteractionFactory(
            company=company,
            companies=[],
            date='2023-08-10',
        )
        interaction_2 = CompanyInteractionFactory(
            company=company,
            companies=[],
            date='2023-08-09',
        )
        referral = CompanyReferralInteractionFactory(
            company=company,
            companies=[],
            company_referral__completed_on='2023-08-08',
        )

        url = reverse(
            'api-v4:company-activity:activity',
            kwargs={'pk': company.pk},
        )
        url = f'{url}?limit=2&offset=1'

        response = self.api_client.post(url)
        response_data = response.json()

        assert response_data['activities']['count'] == 3
        assert len(response_data['activities']['results']) == 2

        returned_ids = [
            response.get('id') for response in response_data['activities']['results']
        ]
        assert str(interaction_2.id) in returned_ids
        assert str(referral.id) in returned_ids

    def test_endpoint__sorting(self):
        """Test activity endpoint sorts correctly based on request param"""
        company = CompanyFactory()
        interaction_1 = CompanyInteractionFactory(
            company=company,
            companies=[],
            date='2023-08-10',
        )
        interaction_2 = CompanyInteractionFactory(
            company=company,
            companies=[],
            date='2023-08-09',
        )
        referral = CompanyReferralInteractionFactory(
            company=company,
            companies=[],
            company_referral__completed_on='2023-08-08',
        )

        url = reverse(
            'api-v4:company-activity:activity',
            kwargs={'pk': company.pk},
        )

        payload = {
            'sortby': 'date:desc',
        }

        response = self.api_client.post(url, data=payload)
        response_data = response.json()

        returned_ids = [
            response.get('id') for response in response_data['activities']['results']
        ]
        assert returned_ids == [
            str(interaction_1.id),
            str(interaction_2.id),
            str(referral.id),
        ]

        payload = {
            'sortby': 'date:asc',
        }

        response = self.api_client.post(url, data=payload)
        response_data = response.json()

        returned_ids = [
            response.get('id') for response in response_data['activities']['results']
        ]
        assert returned_ids == [
            str(referral.id),
            str(interaction_2.id),
            str(interaction_1.id),
        ]

    def test_endpoint__has_company_referrals(self):
        """Test activity endpoint returns referral interactions for given company"""
        company = CompanyFactory()
        interaction = CompanyReferralInteractionFactory(company=company, companies=[])
        CompanyReferralInteractionFactory(company=company, companies=[])

        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = self.api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['activities']['results']) == 2

        activtiy = [
            activity
            for activity in response_data['activities']['results']
            if activity['id'] == str(interaction.id)
        ][0]

        assert activtiy['id'] == str(interaction.id)
        assert activtiy['activity_source'] == 'referral'
        assert (
            activtiy['company_referral']['recipient']['name']
            == interaction.company_referral.recipient.name
        )
        assert (
            activtiy['company_referral']['status']
            == interaction.company_referral.status
        )
        assert (
            activtiy['company_referral']['subject']
            == interaction.company_referral.subject
        )
        assert (
            activtiy['company_referral']['notes'] == interaction.company_referral.notes
        )

    def test_endpoint__has_referrals_for_given_company_only(self):
        """Test activity endpoint returns referrals for given company only"""
        company = CompanyFactory()
        interaction = CompanyReferralInteractionFactory(company=company, companies=[])
        CompanyReferralInteractionFactory(companies=[])

        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = self.api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['activities']['results']) == 1

        assert response_data['activities']['results'][0]['id'] == str(interaction.id)

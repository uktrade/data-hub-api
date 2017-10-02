import pytest
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin
from datahub.interaction.test.factories import InteractionFactory
from datahub.investment.test.factories import InvestmentProjectFactory


class TestInteraction(APITestMixin):
    """Interaction test case."""

    def test_interaction_detail_view(self):
        """Interaction detail view."""
        interaction = InteractionFactory()
        url = reverse('api-v1:interaction-detail', kwargs={'pk': interaction.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(interaction.pk)

    @freeze_time('2017-04-18 13:25:30.986208+00:00')
    def test_add_interaction(self):
        """Test add new interaction."""
        adviser = AdviserFactory()
        url = reverse('api-v1:interaction-list')
        response = self.api_client.post(url, {
            'communication_channel': constants.InteractionType.face_to_face.value.id,
            'subject': 'whatever',
            'date': now().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': CompanyFactory().pk,
            'contact': ContactFactory().pk,
            'service': constants.Service.trade_enquiry.value.id,
            'dit_team': constants.Team.healthcare_uk.value.id
        })

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['dit_adviser'] == str(adviser.pk)
        assert response_data['modified_on'] == '2017-04-18T13:25:30.986208'
        assert response_data['created_on'] == '2017-04-18T13:25:30.986208'

    def test_add_interaction_project_missing_fields(self):
        """Tests add new interaction without RequiredUnlessAlreadyBlank fields."""
        url = reverse('api-v1:interaction-list')
        response = self.api_client.post(url, {
            'subject': 'whatever',
            'date': now().isoformat(),
            'notes': 'hello',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'dit_team': ['This field is required.'],
            'communication_channel': ['This field is required.'],
            'service': ['This field is required.']
        }

    @freeze_time('2017-04-18 13:25:30.986208+00:00')
    def test_add_interaction_project(self):
        """Test add new interaction for an investment project."""
        project = InvestmentProjectFactory()
        adviser = AdviserFactory()
        url = reverse('api-v1:interaction-list')
        response = self.api_client.post(url, {
            'communication_channel': constants.InteractionType.face_to_face.value.id,
            'subject': 'whatever',
            'date': now().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'investment_project': project.pk,
            'service': constants.Service.trade_enquiry.value.id,
            'dit_team': constants.Team.healthcare_uk.value.id
        })

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['dit_adviser'] == str(adviser.pk)
        assert response_data['investment_project'] == str(project.pk)
        assert response_data['modified_on'] == '2017-04-18T13:25:30.986208'
        assert response_data['created_on'] == '2017-04-18T13:25:30.986208'

    def test_add_interaction_no_entity(self):
        """Test add new interaction without a contact, company or
        investment project.
        """
        url = reverse('api-v1:interaction-list')
        response = self.api_client.post(url, {
            'communication_channel': constants.InteractionType.face_to_face.value.id,
            'subject': 'whatever',
            'date': now().isoformat(),
            'dit_adviser': AdviserFactory().pk,
            'notes': 'hello',
            'service': constants.Service.trade_enquiry.value.id,
            'dit_team': constants.Team.healthcare_uk.value.id
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'non_field_errors': [
                'One or more of company, investment_project must be provided.'
            ]
        }

    @pytest.mark.parametrize('field,value', (
        ('dit_team', constants.Team.crm.value.id),
        ('communication_channel', constants.InteractionType.email_website.value.id),
        ('service', constants.Service.trade_enquiry.value.id)
    ))
    def test_update_non_null_field_to_null(self, field, value):
        """
        Tests setting fields to null that are currently non-null, and are allowed to be null
        when already null.
        """
        creation_data = {
            'subject': 'whatever',
            'date': now().isoformat(),
            'dit_adviser_id': AdviserFactory().pk,
            'notes': 'hello',
            f'{field}_id': value
        }
        interaction = InteractionFactory(**creation_data)

        url = reverse('api-v1:interaction-detail', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            field: None,
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            field: ['This field is required.'],
        }

    @pytest.mark.parametrize('field', ('dit_team', 'communication_channel', 'service',))
    def test_update_null_field_to_null(self, field):
        """
        Tests setting fields to null that are currently null, and are allowed to be null
        when already null.
        """
        creation_data = {
            'subject': 'whatever',
            'date': now().isoformat(),
            'dit_adviser_id': AdviserFactory().pk,
            'notes': 'hello',
            f'{field}_id': None
        }
        interaction = InteractionFactory(**creation_data)

        url = reverse('api-v1:interaction-detail', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            field: None,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.json()[field] is None

    def test_modify_interaction(self):
        """Modify an existing interaction."""
        interaction = InteractionFactory(subject='I am a subject')

        url = reverse('api-v1:interaction-detail', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            'subject': 'I am another subject',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'

    def test_list_filtered_company(self):
        """List of interactions filtered by company"""
        company1 = CompanyFactory()
        company2 = CompanyFactory()

        InteractionFactory.create_batch(3, company=company1)
        interactions = InteractionFactory.create_batch(2, company=company2)

        url = reverse('api-v1:interaction-list')
        response = self.api_client.get(url, {'company_id': company2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert {i['id'] for i in response.data['results']} == {str(i.id) for i in interactions}

    def test_list_filtered_contact(self):
        """List of interactions filtered by contact"""
        contact1 = ContactFactory()
        contact2 = ContactFactory()

        InteractionFactory.create_batch(3, contact=contact1)
        interactions = InteractionFactory.create_batch(2, contact=contact2)

        url = reverse('api-v1:interaction-list')
        response = self.api_client.get(url, {'contact_id': contact2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert {i['id'] for i in response.data['results']} == {str(i.id) for i in interactions}

    def test_list_filtered_investment_project(self):
        """List of interactions filtered by investment project"""
        contact = ContactFactory()
        project = InvestmentProjectFactory()
        company = CompanyFactory()

        InteractionFactory.create_batch(3, contact=contact)
        InteractionFactory.create_batch(3, company=company)
        project_interactions = InteractionFactory.create_batch(
            2, investment_project=project
        )

        url = reverse('api-v1:interaction-list')
        response = self.api_client.get(url, {
            'investment_project_id': project.id
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in project_interactions}
        assert actual_ids == expected_ids

from datetime import date
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import InteractionType, Service, Team
from datahub.core.test_utils import APITestMixin
from datahub.interaction.test.factories import InteractionFactory
from datahub.investment.test.factories import InvestmentProjectFactory


class TestInteractionV3(APITestMixin):
    """Tests for v3 interaction views."""

    def test_interaction_detail_view(self):
        """Interaction detail view."""
        interaction = InteractionFactory()
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(interaction.pk)

    @freeze_time('2017-04-18 13:25:30.986208+00:00')
    def test_add_interaction(self):
        """Test add new interaction."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'interaction_type': InteractionType.face_to_face.value.id,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'interaction_type': {
                'id': InteractionType.face_to_face.value.id,
                'name': InteractionType.face_to_face.value.name
            },
            'subject': 'whatever',
            'date': '2017-04-18',
            'dit_adviser': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name
            },
            'notes': 'hello',
            'company': {
                'id': str(company.pk),
                'name': company.name
            },
            'contact': {
                'id': str(contact.pk),
                'name': contact.name
            },
            'service': {
                'id': str(Service.trade_enquiry.value.id),
                'name': Service.trade_enquiry.value.name,
            },
            'dit_team': {
                'id': str(Team.healthcare_uk.value.id),
                'name': Team.healthcare_uk.value.name,
            },
            'investment_project': None,
            'created_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'modified_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'created_on': '2017-04-18T13:25:30.986208',
            'modified_on': '2017-04-18T13:25:30.986208'
        }

    def test_add_interaction_project_missing_fields(self):
        """Test validation of missing fields."""
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'date': ['This field is required.'],
            'dit_adviser': ['This field is required.'],
            'dit_team': ['This field is required.'],
            'interaction_type': ['This field is required.'],
            'notes': ['This field is required.'],
            'service': ['This field is required.'],
            'subject': ['This field is required.'],
        }

    @freeze_time('2017-04-18 13:25:30.986208+00:00')
    def test_add_interaction_project(self):
        """Test add new interaction for an investment project."""
        project = InvestmentProjectFactory()
        adviser = AdviserFactory()
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {
            'interaction_type': InteractionType.face_to_face.value.id,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'investment_project': project.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['dit_adviser']['id'] == str(adviser.pk)
        assert response_data['investment_project']['id'] == str(project.pk)
        assert response_data['modified_on'] == '2017-04-18T13:25:30.986208'
        assert response_data['created_on'] == '2017-04-18T13:25:30.986208'

    def test_add_interaction_no_entity(self):
        """Test add new interaction without a contact, company or
        investment project.
        """
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {
            'interaction_type': InteractionType.face_to_face.value.id,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': AdviserFactory().pk,
            'notes': 'hello',
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'non_field_errors': [
                'One or more of company, investment_project must be provided.'
            ]
        }

    def test_modify_interaction(self):
        """Modify an existing interaction."""
        interaction = InteractionFactory(subject='I am a subject')

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            'subject': 'I am another subject',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'

    def test_date_validation(self):
        """Test validation when an invalid date is provided."""
        interaction = InteractionFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            'date': 'abcd-de-fe',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['date'] == [
            'Datetime has wrong format. Use one of these formats instead: YYYY-MM-DD.'
        ]

    def test_list_filtered_company(self):
        """List of interactions filtered by company"""
        company1 = CompanyFactory()
        company2 = CompanyFactory()

        InteractionFactory.create_batch(3, company=company1)
        interactions = InteractionFactory.create_batch(2, company=company2)

        url = reverse('api-v3:interaction:collection')
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

        url = reverse('api-v3:interaction:collection')
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

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, {
            'investment_project_id': project.id
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in project_interactions}
        assert actual_ids == expected_ids

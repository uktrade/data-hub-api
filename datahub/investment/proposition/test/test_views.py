from uuid import UUID

import factory
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin
from datahub.investment.proposition.models import Proposition
from datahub.investment.test.factories import InvestmentProjectFactory
from .factories import PropositionFactory


class TestCreateProposition(APITestMixin):
    """Base tests for the create proposition view."""

    def test_can_create_proposition(self):
        """Test creating proposition."""
        adviser = AdviserFactory()
        investment_project = InvestmentProjectFactory()

        url = reverse('api-v3:investment:proposition:collection')
        response = self.api_client.post(
            url,
            {
                'investment_project': investment_project.pk,
                'name': 'My proposition.',
                'scope': 'Very broad scope.',
                'adviser': adviser.pk,
                'deadline': '2018-02-10',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        instance = Proposition.objects.get(pk=UUID(response_data['id']))
        assert response_data == {
            'id': str(instance.pk),
            'investment_project': {
                'name': investment_project.name,
                'project_code': investment_project.project_code,
                'id': str(investment_project.pk),
            },
            'adviser': {
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
                'id': str(adviser.pk),
            },
            'deadline': '2018-02-10',
            'status': 'ongoing',
            'name': 'My proposition.',
            'scope': 'Very broad scope.',
            'reason_abandoned': '',
            'created_on': instance.created_on.isoformat().replace('+00:00', 'Z'),
            'created_by': {
                'first_name': instance.created_by.first_name,
                'last_name': instance.created_by.last_name,
                'name': instance.created_by.name,
                'id': str(instance.created_by.pk),
            },
            'abandoned_on': None,
            'abandoned_by': None,
            'completed_details': '',
            'completed_on': None,
            'completed_by': None
        }

    def test_cannot_created_with_fields_missing(self):
        """Test that proposition cannot be created without required fields."""
        url = reverse('api-v3:investment:proposition:collection')
        response = self.api_client.post(
            url,
            {
            },
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'investment_project': ['This field is required.'],
            'adviser': ['This field is required.'],
            'deadline': ['This field is required.'],
            'name': ['This field is required.'],
            'scope': ['This field is required.'],
        }

    def test_deadline_validation(self):
        """Test validation when an invalid date is provided."""
        adviser = AdviserFactory()
        investment_project = InvestmentProjectFactory()

        url = reverse('api-v3:investment:proposition:collection')
        response = self.api_client.post(url, {
            'investment_project': investment_project.pk,
            'name': 'My proposition.',
            'scope': 'Very broad scope.',
            'adviser': adviser.pk,
            'deadline': 'abcd-de-fe',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['deadline'] == [
            'Date has wrong format. Use one of these formats instead: YYYY[-MM[-DD]].'
        ]


class TestUpdateProposition(APITestMixin):
    """Base tests for the update proposition view."""

    @pytest.mark.parametrize(
        'method', ('put', 'patch',),
    )
    def test_cannot_update_collection(self, method):
        """Test cannot update proposition."""
        url = reverse('api-v3:investment:proposition:collection')
        response = getattr(self.api_client, method)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.parametrize(
        'method', ('put', 'patch',),
    )
    def test_cannot_update_item(self, method):
        """Test cannot update given proposition."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:item', kwargs={'pk': proposition.pk})
        response = getattr(self.api_client, method)(url, {
            'name': 'hello!',
        }, format='json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestListPropositions(APITestMixin):
    """Tests for the list propositions view."""

    def test_filtered_by_investment_project(self):
        """List of propositions filtered by investment project."""
        investment_project = InvestmentProjectFactory()

        PropositionFactory.create_batch(3)
        propositions = PropositionFactory.create_batch(
            3, investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:collection')
        response = self.api_client.get(url, {
            'investment_project_id': investment_project.id
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in propositions}
        assert actual_ids == expected_ids

    def test_filtered_by_adviser(self):
        """List of propositions filtered by adviser."""
        adviser = AdviserFactory()

        PropositionFactory.create_batch(3)
        propositions = PropositionFactory.create_batch(
            3, adviser=adviser
        )

        url = reverse('api-v3:investment:proposition:collection')
        response = self.api_client.get(url, {
            'adviser_id': adviser.id
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in propositions}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize(
        'proposition_status',
        (
            'ongoing',
            'abandoned',
            'completed',
        )
    )
    def test_filtered_by_status(self, proposition_status):
        """List of propositions filtered by status."""
        statuses = ('ongoing', 'abandoned', 'completed',)

        PropositionFactory.create_batch(
            3, status=factory.Iterator(statuses)
        )

        url = reverse('api-v3:investment:proposition:collection')
        response = self.api_client.get(url, {
            'status': proposition_status
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['status'] == proposition_status


class TestGetProposition(APITestMixin):
    """Base tests for get proposition view."""

    def test_fails_without_permissions(self, api_client):
        """Should return 403"""
        proposition = PropositionFactory()
        url = reverse('api-v3:investment:proposition:item', kwargs={'pk': proposition.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_can_get_proposition(self):
        """Test get proposition."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:item', kwargs={'pk': proposition.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': str(proposition.pk),
            'investment_project': {
                'name': proposition.investment_project.name,
                'project_code': proposition.investment_project.project_code,
                'id': str(proposition.investment_project.pk),
            },
            'adviser': {
                'first_name': proposition.adviser.first_name,
                'last_name': proposition.adviser.last_name,
                'name': proposition.adviser.name,
                'id': str(proposition.adviser.pk)
            },
            'deadline': '2018-05-20',
            'status': 'ongoing',
            'name': proposition.name,
            'scope': proposition.scope,
            'reason_abandoned': '',
            'created_on': proposition.created_on.isoformat().replace('+00:00', 'Z'),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'abandoned_on': None,
            'abandoned_by': None,
            'completed_details': '',
            'completed_on': None,
            'completed_by': None,
        }


class TestCompleteProposition(APITestMixin):
    """Base tests for the complete proposition view."""

    def test_can_complete_proposition(self):
        """Test completing proposition."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:complete', kwargs={'pk': proposition.pk})
        response = self.api_client.post(
            url,
            {
                'completed_details': 'All done 100% satisfaction.',
            },
            format='json',
        )
        proposition.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': str(proposition.pk),
            'investment_project': {
                'name': proposition.investment_project.name,
                'project_code': proposition.investment_project.project_code,
                'id': str(proposition.investment_project.pk)
            },
            'adviser': {
                'first_name': proposition.adviser.first_name,
                'last_name': proposition.adviser.last_name,
                'name': proposition.adviser.name,
                'id': str(proposition.adviser.pk)
            },
            'deadline': '2018-05-20',
            'status': 'completed',
            'name': proposition.name,
            'scope': proposition.scope,
            'reason_abandoned': '',
            'created_on': proposition.created_on.isoformat().replace('+00:00', 'Z'),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'abandoned_on': None,
            'abandoned_by': None,
            'completed_details': 'All done 100% satisfaction.',
            'completed_on': proposition.completed_on.isoformat().replace('+00:00', 'Z'),
            'completed_by': {
                'first_name': proposition.completed_by.first_name,
                'last_name': proposition.completed_by.last_name,
                'name': proposition.completed_by.name,
                'id': str(proposition.completed_by.pk),
            }
        }

    @pytest.mark.parametrize(
        'proposition_status', ('completed', 'abandoned',),
    )
    def test_cannot_complete_proposition_without_ongoing_status(self, proposition_status):
        """Test cannot complete proposition that doesn't have ongoing status."""
        proposition = PropositionFactory(
            status=proposition_status
        )
        url = reverse('api-v3:investment:proposition:complete', kwargs={'pk': proposition.pk})
        response = self.api_client.post(
            url,
            {
                'completed_details': 'All done 100% satisfaction.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        response_data = response.json()
        detail = f'The action cannot be performed in the current status {proposition_status}.'
        assert response_data['detail'] == detail

        proposition.refresh_from_db()
        assert proposition.status == proposition_status
        assert proposition.completed_by is None
        assert proposition.completed_on is None


class TestAbandonProposition(APITestMixin):
    """Base tests for the abandon proposition view."""

    def test_can_abandon_proposition(self):
        """Test abandoning proposition."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:abandon', kwargs={'pk': proposition.pk})
        response = self.api_client.post(
            url,
            {
                'reason_abandoned': 'Not enough information.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        proposition.refresh_from_db()
        response_data = response.json()
        assert response_data == {
            'id': str(proposition.pk),
            'investment_project': {
                'name': proposition.investment_project.name,
                'project_code': proposition.investment_project.project_code,
                'id': str(proposition.investment_project.pk),
            },
            'adviser': {
                'first_name': proposition.adviser.first_name,
                'last_name': proposition.adviser.last_name,
                'name': proposition.adviser.name,
                'id': str(proposition.adviser.pk)
            },
            'deadline': '2018-05-20',
            'status': 'abandoned',
            'name': proposition.name,
            'scope': proposition.scope,
            'reason_abandoned': proposition.reason_abandoned,
            'created_on': proposition.created_on.isoformat().replace('+00:00', 'Z'),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'abandoned_on': proposition.abandoned_on.isoformat().replace('+00:00', 'Z'),
            'abandoned_by': {
                'first_name': proposition.abandoned_by.first_name,
                'last_name': proposition.abandoned_by.last_name,
                'name': proposition.abandoned_by.name,
                'id': str(proposition.abandoned_by.pk),
            },
            'completed_details': '',
            'completed_on': None,
            'completed_by': None,
        }

    @pytest.mark.parametrize(
        'proposition_status', ('completed', 'abandoned',),
    )
    def test_cannot_abandon_proposition_without_ongoing_status(self, proposition_status):
        """Test cannot abandon proposition that doesn't have ongoing status."""
        proposition = PropositionFactory(
            status=proposition_status
        )
        url = reverse('api-v3:investment:proposition:abandon', kwargs={'pk': proposition.pk})
        response = self.api_client.post(
            url,
            {
                'reason_abandoned': 'Too many cats.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        response_data = response.json()
        detail = f'The action cannot be performed in the current status {proposition_status}.'
        assert response_data['detail'] == detail

        proposition.refresh_from_db()
        assert proposition.status == proposition_status
        assert proposition.abandoned_by is None
        assert proposition.abandoned_on is None

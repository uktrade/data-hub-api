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
    """Tests for the create proposition view."""

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
        instance = Proposition.objects.get(pk=response_data['id'])
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
            'details': '',
            'created_on': instance.created_on.isoformat().replace('+00:00', 'Z'),
            'created_by': {
                'first_name': instance.created_by.first_name,
                'last_name': instance.created_by.last_name,
                'name': instance.created_by.name,
                'id': str(instance.created_by.pk),
            },
            'modified_by': {
                'first_name': instance.modified_by.first_name,
                'last_name': instance.modified_by.last_name,
                'name': instance.modified_by.name,
                'id': str(instance.modified_by.pk),
            },
            'modified_on': instance.modified_on.isoformat().replace('+00:00', 'Z'),
        }

    def test_cannot_created_with_fields_missing(self):
        """Test that proposition cannot be created without required fields."""
        url = reverse('api-v3:investment:proposition:collection')
        response = self.api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'investment_project': ['This field is required.'],
            'adviser': ['This field is required.'],
            'deadline': ['This field is required.'],
            'name': ['This field is required.'],
            'scope': ['This field is required.'],
        }


class TestUpdateProposition(APITestMixin):
    """Tests for the update proposition view."""

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
    """Tests for get proposition view."""

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
            'deadline': proposition.deadline.isoformat(),
            'status': 'ongoing',
            'name': proposition.name,
            'scope': proposition.scope,
            'details': '',
            'created_on': proposition.created_on.isoformat().replace('+00:00', 'Z'),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'modified_on': proposition.modified_on.isoformat().replace('+00:00', 'Z'),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            },
        }


class TestCompleteProposition(APITestMixin):
    """Tests for the complete proposition view."""

    def test_can_complete_proposition(self):
        """Test completing proposition."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:complete', kwargs={'pk': proposition.pk})
        response = self.api_client.post(
            url,
            {
                'details': 'All done 100% satisfaction.',
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
            'deadline': proposition.deadline.isoformat(),
            'status': 'completed',
            'name': proposition.name,
            'scope': proposition.scope,
            'created_on': proposition.created_on.isoformat().replace('+00:00', 'Z'),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'details': 'All done 100% satisfaction.',
            'modified_on': proposition.modified_on.isoformat().replace('+00:00', 'Z'),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
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
                'details': 'All done 100% satisfaction.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        response_data = response.json()
        detail = f'The action cannot be performed in the current status {proposition_status}.'
        assert response_data['detail'] == detail

        proposition.refresh_from_db()
        assert proposition.status == proposition_status
        assert proposition.details == ''


class TestAbandonProposition(APITestMixin):
    """Tests for the abandon proposition view."""

    def test_can_abandon_proposition(self):
        """Test abandoning proposition."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:abandon', kwargs={'pk': proposition.pk})
        response = self.api_client.post(
            url,
            {
                'details': 'Not enough information.',
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
            'deadline': proposition.deadline.isoformat(),
            'status': 'abandoned',
            'name': proposition.name,
            'scope': proposition.scope,
            'created_on': proposition.created_on.isoformat().replace('+00:00', 'Z'),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'details': proposition.details,
            'modified_on': proposition.modified_on.isoformat().replace('+00:00', 'Z'),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            },
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
                'details': 'Too many cats.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        response_data = response.json()
        detail = f'The action cannot be performed in the current status {proposition_status}.'
        assert response_data['detail'] == detail

        proposition.refresh_from_db()
        assert proposition.status == proposition_status
        assert proposition.details == ''

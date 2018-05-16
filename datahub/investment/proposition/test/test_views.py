import uuid

import factory
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.investment.proposition.constants import PropositionStatus
from datahub.investment.proposition.models import Proposition, PropositionPermission
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory
from .factories import PropositionFactory

NON_RESTRICTED_READ_PERMISSIONS = (
    (
        PropositionPermission.read_all,
    ),
    (
        PropositionPermission.read_all,
        PropositionPermission.read_associated_investmentproject,
    )
)


NON_RESTRICTED_ADD_PERMISSIONS = (
    (
        PropositionPermission.add_all,
    ),
    (
        PropositionPermission.add_all,
        PropositionPermission.add_associated_investmentproject,
    )
)


NON_RESTRICTED_CHANGE_PERMISSIONS = (
    (
        PropositionPermission.change_all,
    ),
    (
        PropositionPermission.change_all,
        PropositionPermission.change_associated_investmentproject,
    )
)


class TestCreateProposition(APITestMixin):
    """Tests for the create proposition view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    def test_can_create_proposition(self, permissions):
        """Test creating proposition."""
        investment_project = InvestmentProjectFactory()

        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        adviser = create_test_user(
            permission_codenames=permissions,
        )
        api_client = self.create_api_client(user=adviser)

        response = api_client.post(
            url,
            {
                'name': 'My proposition.',
                'scope': 'Very broad scope.',
                'assigned_to': adviser.pk,
                'deadline': '2018-02-10',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        instance = Proposition.objects.get(pk=response_data['id'])
        assert instance.created_by == adviser
        assert instance.modified_by == adviser
        assert response_data == {
            'id': str(instance.pk),
            'investment_project': {
                'name': investment_project.name,
                'project_code': investment_project.project_code,
                'id': str(investment_project.pk),
            },
            'assigned_to': {
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
                'id': str(adviser.pk),
            },
            'deadline': '2018-02-10',
            'status': PropositionStatus.ongoing,
            'name': 'My proposition.',
            'scope': 'Very broad scope.',
            'details': '',
            'created_on': format_date_or_datetime(instance.created_on),
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
            'modified_on': format_date_or_datetime(instance.modified_on),
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    def test_cannot_create_proposition_for_non_existent_investment_project(self, permissions):
        """Test user cannot create proposition for non existent investment project."""
        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': uuid.uuid4(),
        })

        adviser = create_test_user(
            permission_codenames=permissions,
        )
        api_client = self.create_api_client(user=adviser)

        response = api_client.post(
            url,
            {
                'name': 'My proposition.',
                'scope': 'Very broad scope.',
                'assigned_to': adviser.pk,
                'deadline': '2018-02-10',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

    def test_restricted_user_can_create_associated_investment_project_proposition(self):
        """Test restricted user can create associated invesment project proposition."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(created_by=project_creator)

        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        adviser = create_test_user(
            permission_codenames=[PropositionPermission.add_associated_investmentproject],
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=adviser)
        response = api_client.post(
            url,
            {
                'name': 'My proposition.',
                'scope': 'Very broad scope.',
                'assigned_to': adviser.pk,
                'deadline': '2018-02-10',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        instance = Proposition.objects.get(pk=response_data['id'])
        assert instance.created_by == adviser
        assert instance.modified_by == adviser
        assert response_data == {
            'id': str(instance.pk),
            'investment_project': {
                'name': investment_project.name,
                'project_code': investment_project.project_code,
                'id': str(investment_project.pk),
            },
            'assigned_to': {
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
                'id': str(adviser.pk),
            },
            'deadline': '2018-02-10',
            'status': PropositionStatus.ongoing,
            'name': 'My proposition.',
            'scope': 'Very broad scope.',
            'details': '',
            'created_on': format_date_or_datetime(instance.created_on),
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
            'modified_on': format_date_or_datetime(instance.modified_on),
        }

    def test_restricted_user_cannot_create_non_associated_investment_project_proposition(self):
        """Test restricted user cannot create non associated invesment project proposition."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(created_by=project_creator)

        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        adviser = create_test_user(
            permission_codenames=[PropositionPermission.add_associated_investmentproject],
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=adviser)
        response = api_client.post(
            url,
            {
                'name': 'My proposition.',
                'scope': 'Very broad scope.',
                'assigned_to': adviser.pk,
                'deadline': '2018-02-10',
            },
            format='json',
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {
            'investment_project': [
                "You don't have permission to add a proposition for this investment project."
            ]
        }

    def test_cannot_created_with_fields_missing(self):
        """Test that proposition cannot be created without required fields."""
        investment_project = InvestmentProjectFactory()

        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk
        })
        response = self.api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'assigned_to': ['This field is required.'],
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
        investment_project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk
        })
        response = getattr(self.api_client, method)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.parametrize(
        'method', ('put', 'patch',),
    )
    def test_cannot_update_item(self, method):
        """Test cannot update given proposition."""
        proposition = PropositionFactory()
        investment_project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:proposition:item', kwargs={
            'pk': proposition.pk,
            'project_pk': investment_project.pk,
        })
        response = getattr(self.api_client, method)(url, {
            'name': 'hello!',
        }, format='json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestListPropositions(APITestMixin):
    """Tests for the list propositions view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    def test_non_restricted_user_can_list_propositions(self, permissions):
        """List of propositions by a non restricted user."""
        investment_project = InvestmentProjectFactory()

        PropositionFactory.create_batch(3)
        propositions = PropositionFactory.create_batch(
            3, investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in propositions}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    def test_user_cannot_list_propositions_for_non_existent_investment_project(self, permissions):
        """Test user cannot list propositions for a non existent investment project."""
        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': uuid.uuid4(),
        })

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

    def test_restricted_user_can_list_propositions(self):
        """List of propositions by a restricted user."""
        PropositionFactory.create_batch(3)

        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        propositions = PropositionFactory.create_batch(
            3, investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.read_associated_investmentproject,
            ),
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in propositions}
        assert actual_ids == expected_ids

    def test_restricted_user_cannot_list_non_associated_ip_propositions(self):
        """Restricted user cannot list non associated investment project propositions."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        PropositionFactory.create_batch(
            3, investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.read_associated_investmentproject
            ),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_data = response.json()
        assert response_data == {
            'detail': 'You do not have permission to perform this action.'
        }

    def test_filtered_by_adviser(self):
        """List of propositions filtered by assigned adviser."""
        adviser = AdviserFactory()
        investment_project = InvestmentProjectFactory()

        PropositionFactory.create_batch(
            3, investment_project=investment_project
        )
        propositions = PropositionFactory.create_batch(
            3,
            assigned_to=adviser,
            investment_project=investment_project,
        )

        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk,
        })
        response = self.api_client.get(url, {
            'assigned_to_id': adviser.id
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
            PropositionStatus.ongoing,
            PropositionStatus.abandoned,
            PropositionStatus.completed,
        )
    )
    def test_filtered_by_status(self, proposition_status):
        """List of propositions filtered by status."""
        statuses = (
            PropositionStatus.ongoing,
            PropositionStatus.abandoned,
            PropositionStatus.completed,
        )
        investment_project = InvestmentProjectFactory()
        PropositionFactory.create_batch(
            3,
            status=factory.Iterator(statuses),
            investment_project=investment_project,
        )

        url = reverse('api-v3:investment:proposition:collection', kwargs={
            'project_pk': investment_project.pk,
        })
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
        """Should return 401"""
        proposition = PropositionFactory()
        url = reverse('api-v3:investment:proposition:item', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    def test_non_restricted_user_can_get_proposition(self, permissions):
        """Test get proposition by a non restricted user."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:item', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': str(proposition.pk),
            'investment_project': {
                'name': proposition.investment_project.name,
                'project_code': proposition.investment_project.project_code,
                'id': str(proposition.investment_project.pk),
            },
            'assigned_to': {
                'first_name': proposition.assigned_to.first_name,
                'last_name': proposition.assigned_to.last_name,
                'name': proposition.assigned_to.name,
                'id': str(proposition.assigned_to.pk)
            },
            'deadline': proposition.deadline.isoformat(),
            'status': PropositionStatus.ongoing,
            'name': proposition.name,
            'scope': proposition.scope,
            'details': '',
            'created_on': format_date_or_datetime(proposition.created_on),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'modified_on': format_date_or_datetime(proposition.modified_on),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            },
        }

    def test_restricted_user_can_get_proposition(self):
        """Test get proposition by a restricted user."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        proposition = PropositionFactory(
            investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:item', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })
        user = create_test_user(
            permission_codenames=(
                PropositionPermission.read_associated_investmentproject,
            ),
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': str(proposition.pk),
            'investment_project': {
                'name': proposition.investment_project.name,
                'project_code': proposition.investment_project.project_code,
                'id': str(proposition.investment_project.pk),
            },
            'assigned_to': {
                'first_name': proposition.assigned_to.first_name,
                'last_name': proposition.assigned_to.last_name,
                'name': proposition.assigned_to.name,
                'id': str(proposition.assigned_to.pk)
            },
            'deadline': proposition.deadline.isoformat(),
            'status': PropositionStatus.ongoing,
            'name': proposition.name,
            'scope': proposition.scope,
            'details': '',
            'created_on': format_date_or_datetime(proposition.created_on),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'modified_on': format_date_or_datetime(proposition.modified_on),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            },
        }

    def test_restricted_user_cannot_get_non_associated_ip_proposition(self):
        """Test get non associated ip proposition by a restricted user."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        proposition = PropositionFactory(
            investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:item', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })
        user = create_test_user(
            permission_codenames=(
                PropositionPermission.read_associated_investmentproject,
            ),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_data = response.json()
        assert response_data == {
            'detail': 'You do not have permission to perform this action.'
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    def test_user_cannot_get_proposition_for_non_existent_project(self, permissions):
        """Test user cannot get proposition by a non restricted user."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:item', kwargs={
            'pk': proposition.pk,
            'project_pk': uuid.uuid4(),
        })
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}


class TestCompleteProposition(APITestMixin):
    """Tests for the complete proposition view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    def test_non_restricted_user_can_complete_proposition(self, permissions):
        """Test completing proposition by non restricted user."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:complete', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'All done 100% satisfaction.',
            },
            format='json',
        )
        proposition.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert proposition.modified_by == user
        assert response_data == {
            'id': str(proposition.pk),
            'investment_project': {
                'name': proposition.investment_project.name,
                'project_code': proposition.investment_project.project_code,
                'id': str(proposition.investment_project.pk)
            },
            'assigned_to': {
                'first_name': proposition.assigned_to.first_name,
                'last_name': proposition.assigned_to.last_name,
                'name': proposition.assigned_to.name,
                'id': str(proposition.assigned_to.pk)
            },
            'deadline': proposition.deadline.isoformat(),
            'status': PropositionStatus.completed,
            'name': proposition.name,
            'scope': proposition.scope,
            'created_on': format_date_or_datetime(proposition.created_on),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'details': 'All done 100% satisfaction.',
            'modified_on': format_date_or_datetime(proposition.modified_on),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            }
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    def test_user_cannot_complete_proposition_for_non_existent_project(self, permissions):
        """Test user cannot complete proposition for non existent investment project."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:complete', kwargs={
            'pk': proposition.pk,
            'project_pk': uuid.uuid4(),
        })

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'All done 100% satisfaction.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

    def test_restricted_user_can_complete_proposition(self):
        """Test completing proposition by a restricted user."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        proposition = PropositionFactory(
            investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:complete', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.change_associated_investmentproject,
            ),
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'All done 100% satisfaction.',
            },
            format='json',
        )
        proposition.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert proposition.modified_by == user
        assert response_data == {
            'id': str(proposition.pk),
            'investment_project': {
                'name': proposition.investment_project.name,
                'project_code': proposition.investment_project.project_code,
                'id': str(proposition.investment_project.pk)
            },
            'assigned_to': {
                'first_name': proposition.assigned_to.first_name,
                'last_name': proposition.assigned_to.last_name,
                'name': proposition.assigned_to.name,
                'id': str(proposition.assigned_to.pk)
            },
            'deadline': proposition.deadline.isoformat(),
            'status': PropositionStatus.completed,
            'name': proposition.name,
            'scope': proposition.scope,
            'created_on': format_date_or_datetime(proposition.created_on),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'details': 'All done 100% satisfaction.',
            'modified_on': format_date_or_datetime(proposition.modified_on),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            }
        }

    def test_restricted_user_cannot_complete_non_associated_ip_proposition(self):
        """Test restricted user cannot complete non associated investment project proposition."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        proposition = PropositionFactory(
            investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:complete', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.change_associated_investmentproject,
            ),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'All done 100% satisfaction.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_data = response.json()
        assert response_data == {
            'detail': 'You do not have permission to perform this action.'
        }

        proposition.refresh_from_db()
        assert proposition.details == ''
        assert proposition.modified_by != user

    @pytest.mark.parametrize(
        'proposition_status', (
            PropositionStatus.completed, PropositionStatus.abandoned,
        ),
    )
    def test_cannot_complete_proposition_without_ongoing_status(self, proposition_status):
        """Test cannot complete proposition that doesn't have ongoing status."""
        proposition = PropositionFactory(
            status=proposition_status
        )
        url = reverse('api-v3:investment:proposition:complete', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })
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

    def test_cannot_complete_proposition_without_details(self):
        """Test cannot complete proposition without giving details."""
        proposition = PropositionFactory()
        url = reverse('api-v3:investment:proposition:complete', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })
        response = self.api_client.post(
            url,
            {
                'details': '',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['details'] == ['This field may not be blank.']
        proposition.refresh_from_db()
        assert proposition.status == PropositionStatus.ongoing


class TestAbandonProposition(APITestMixin):
    """Tests for the abandon proposition view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    def test_non_restricted_user_can_abandon_proposition(self, permissions):
        """Test abandoning proposition by non restricted user."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:abandon', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'Not enough information.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        proposition.refresh_from_db()
        response_data = response.json()
        assert proposition.modified_by == user
        assert response_data == {
            'id': str(proposition.pk),
            'investment_project': {
                'name': proposition.investment_project.name,
                'project_code': proposition.investment_project.project_code,
                'id': str(proposition.investment_project.pk),
            },
            'assigned_to': {
                'first_name': proposition.assigned_to.first_name,
                'last_name': proposition.assigned_to.last_name,
                'name': proposition.assigned_to.name,
                'id': str(proposition.assigned_to.pk)
            },
            'deadline': proposition.deadline.isoformat(),
            'status': PropositionStatus.abandoned,
            'name': proposition.name,
            'scope': proposition.scope,
            'created_on': format_date_or_datetime(proposition.created_on),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'details': proposition.details,
            'modified_on': format_date_or_datetime(proposition.modified_on),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            },
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    def test_user_cannot_abandon_proposition_for_non_existent_project(self, permissions):
        """Test user cannot abandon proposition for non existent investment project."""
        proposition = PropositionFactory()

        url = reverse('api-v3:investment:proposition:abandon', kwargs={
            'pk': proposition.pk,
            'project_pk': uuid.uuid4(),
        })

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'Not enough information.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

    def test_restricted_user_can_abandon_proposition(self):
        """Test abandoning proposition by restricted user."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        proposition = PropositionFactory(
            investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:abandon', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.change_associated_investmentproject,
            ),
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'Not enough information.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        proposition.refresh_from_db()
        response_data = response.json()
        assert proposition.modified_by == user
        assert response_data == {
            'id': str(proposition.pk),
            'investment_project': {
                'name': proposition.investment_project.name,
                'project_code': proposition.investment_project.project_code,
                'id': str(proposition.investment_project.pk),
            },
            'assigned_to': {
                'first_name': proposition.assigned_to.first_name,
                'last_name': proposition.assigned_to.last_name,
                'name': proposition.assigned_to.name,
                'id': str(proposition.assigned_to.pk)
            },
            'deadline': proposition.deadline.isoformat(),
            'status': PropositionStatus.abandoned,
            'name': proposition.name,
            'scope': proposition.scope,
            'created_on': format_date_or_datetime(proposition.created_on),
            'created_by': {
                'first_name': proposition.created_by.first_name,
                'last_name': proposition.created_by.last_name,
                'name': proposition.created_by.name,
                'id': str(proposition.created_by.pk),
            },
            'details': proposition.details,
            'modified_on': format_date_or_datetime(proposition.modified_on),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            },
        }

    def test_restricted_user_cannot_abandon_non_associated_ip_proposition(self):
        """Test restricted user cannot abandon non associated investment project proposition."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        proposition = PropositionFactory(
            investment_project=investment_project
        )

        url = reverse('api-v3:investment:proposition:abandon', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.change_associated_investmentproject,
            ),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'Not enough information.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_data = response.json()
        assert response_data == {
            'detail': 'You do not have permission to perform this action.'
        }

        proposition.refresh_from_db()
        assert proposition.details == ''
        assert proposition.modified_by != user

    @pytest.mark.parametrize(
        'proposition_status', (
            PropositionStatus.completed, PropositionStatus.abandoned,
        ),
    )
    def test_cannot_abandon_proposition_without_ongoing_status(self, proposition_status):
        """Test cannot abandon proposition that doesn't have ongoing status."""
        proposition = PropositionFactory(
            status=proposition_status
        )
        url = reverse('api-v3:investment:proposition:abandon', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })
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

    def test_cannot_abandon_proposition_without_details(self):
        """Test cannot abandon proposition without giving details."""
        proposition = PropositionFactory()
        url = reverse('api-v3:investment:proposition:abandon', kwargs={
            'pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
        })
        response = self.api_client.post(
            url,
            {
                'details': '',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['details'] == ['This field may not be blank.']
        proposition.refresh_from_db()
        assert proposition.status == PropositionStatus.ongoing

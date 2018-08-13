import uuid

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.investment.evidence.models import (
    EvidenceGroup, EvidenceGroupPermission
)
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory
from .factories import EvidenceGroupFactory

NON_RESTRICTED_READ_PERMISSIONS = (
    (
        EvidenceGroupPermission.read_all,
    ),
    (
        EvidenceGroupPermission.read_all,
        EvidenceGroupPermission.read_associated_investmentproject,
    )
)


NON_RESTRICTED_ADD_PERMISSIONS = (
    (
        EvidenceGroupPermission.add_all,
    ),
    (
        EvidenceGroupPermission.add_all,
        EvidenceGroupPermission.add_associated_investmentproject,
    )
)


NON_RESTRICTED_CHANGE_PERMISSIONS = (
    (
        EvidenceGroupPermission.change_all,
    ),
    (
        EvidenceGroupPermission.change_all,
        EvidenceGroupPermission.change_associated_investmentproject,
    )
)


class TestCreateEvidenceGroup(APITestMixin):
    """Tests for the create evidence group view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    def test_can_create_evidence_group(self, permissions):
        """Test creating evidence group."""
        investment_project = InvestmentProjectFactory()

        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        adviser = create_test_user(
            permission_codenames=permissions,
        )
        api_client = self.create_api_client(user=adviser)

        response = api_client.post(
            url,
            {
                'name': 'My evidence.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        instance = EvidenceGroup.objects.get(pk=response_data['id'])
        assert instance.created_by == adviser
        assert instance.modified_by == adviser
        assert response_data == {
            'id': str(instance.pk),
            'investment_project': {
                'name': investment_project.name,
                'project_code': investment_project.project_code,
                'id': str(investment_project.pk),
            },
            'name': 'My evidence.',
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
    def test_cannot_create_evidence_group_for_non_existent_investment_project(self, permissions):
        """Test user cannot create evidence group for non existent investment project."""
        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': uuid.uuid4(),
        })

        adviser = create_test_user(
            permission_codenames=permissions,
        )
        api_client = self.create_api_client(user=adviser)

        response = api_client.post(
            url,
            {
                'name': 'My evidence.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

    def test_restricted_user_can_create_associated_evidence_group(self):
        """Test restricted user can create associated evidence group."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(created_by=project_creator)

        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        adviser = create_test_user(
            permission_codenames=[EvidenceGroupPermission.add_associated_investmentproject],
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=adviser)
        response = api_client.post(
            url,
            {
                'name': 'My evidence.',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        instance = EvidenceGroup.objects.get(pk=response_data['id'])
        assert instance.created_by == adviser
        assert instance.modified_by == adviser
        assert response_data == {
            'id': str(instance.pk),
            'investment_project': {
                'name': investment_project.name,
                'project_code': investment_project.project_code,
                'id': str(investment_project.pk),
            },
            'name': 'My evidence.',
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

    def test_restricted_user_cannot_create_non_associated_evidence_group(self):
        """Test restricted user cannot create non associated evidence group."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(created_by=project_creator)

        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        adviser = create_test_user(
            permission_codenames=[EvidenceGroupPermission.add_associated_investmentproject],
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=adviser)
        response = api_client.post(
            url,
            {
                'name': 'My evidence.',
            },
            format='json',
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {
            'investment_project': [
                "You don't have permission to add an evidence group for this investment project."
            ]
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    def test_cannot_created_with_fields_missing(self, permissions):
        """Test that evidence group cannot be created without required fields."""
        investment_project = InvestmentProjectFactory()

        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': investment_project.pk
        })

        adviser = create_test_user(
            permission_codenames=permissions,
        )
        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'name': ['This field is required.'],
        }


class TestUpdateEvidenceGroup(APITestMixin):
    """Tests for the update evidence group view."""

    @pytest.mark.parametrize(
        'method', ('put', 'patch',),
    )
    def test_cannot_update_collection(self, method):
        """Test cannot update evidence group."""
        investment_project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': investment_project.pk
        })
        response = getattr(self.api_client, method)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.parametrize(
        'method', ('put', 'patch',),
    )
    def test_cannot_update_item(self, method):
        """Test cannot update given evidence group."""
        evidence_group = EvidenceGroupFactory()
        investment_project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:evidence-group:item', kwargs={
            'evidence_group_pk': evidence_group.pk,
            'project_pk': investment_project.pk,
        })
        response = getattr(self.api_client, method)(url, {
            'name': 'hello!',
        }, format='json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestListEvidenceGroups(APITestMixin):
    """Tests for the list evidence groups view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    def test_non_restricted_user_can_list_evidence_groups(self, permissions):
        """List of evidence groups by a non restricted user."""
        investment_project = InvestmentProjectFactory()

        EvidenceGroupFactory.create_batch(3)
        evidence_groups = EvidenceGroupFactory.create_batch(
            3, investment_project=investment_project
        )

        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in evidence_groups}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    def test_user_cannot_list_evidence_groups_for_non_existent_investment_project(
            self, permissions
    ):
        """Test user cannot list evidence groups for a non existent investment project."""
        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': uuid.uuid4(),
        })

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

    def test_restricted_user_can_list_evidence_groups(self):
        """List of evidence groups by a restricted user."""
        EvidenceGroupFactory.create_batch(3)

        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        evidence_groups = EvidenceGroupFactory.create_batch(
            3, investment_project=investment_project
        )

        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        user = create_test_user(
            permission_codenames=(
                EvidenceGroupPermission.read_associated_investmentproject,
            ),
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in evidence_groups}
        assert actual_ids == expected_ids

    def test_restricted_user_cannot_list_non_associated_evidence_groups(self):
        """Restricted user cannot list non associated evidence groups."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        EvidenceGroupFactory.create_batch(
            3, investment_project=investment_project
        )

        url = reverse('api-v3:investment:evidence-group:collection', kwargs={
            'project_pk': investment_project.pk,
        })

        user = create_test_user(
            permission_codenames=(
                EvidenceGroupPermission.read_associated_investmentproject
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


class TestGetEvidenceGroup(APITestMixin):
    """Tests for get evidence group view."""

    def test_fails_without_permissions(self, api_client):
        """Should return 401"""
        evidence_group = EvidenceGroupFactory()
        url = reverse('api-v3:investment:evidence-group:item', kwargs={
            'evidence_group_pk': evidence_group.pk,
            'project_pk': evidence_group.investment_project.pk,
        })
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    def test_non_restricted_user_can_get_evidence_group(self, permissions):
        """Test get evidence group by a non restricted user."""
        evidence_group = EvidenceGroupFactory()

        url = reverse('api-v3:investment:evidence-group:item', kwargs={
            'evidence_group_pk': evidence_group.pk,
            'project_pk': evidence_group.investment_project.pk,
        })
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': str(evidence_group.pk),
            'investment_project': {
                'name': evidence_group.investment_project.name,
                'project_code': evidence_group.investment_project.project_code,
                'id': str(evidence_group.investment_project.pk),
            },
            'name': evidence_group.name,
            'created_on': format_date_or_datetime(evidence_group.created_on),
            'created_by': {
                'first_name': evidence_group.created_by.first_name,
                'last_name': evidence_group.created_by.last_name,
                'name': evidence_group.created_by.name,
                'id': str(evidence_group.created_by.pk),
            },
            'modified_on': format_date_or_datetime(evidence_group.modified_on),
            'modified_by': {
                'first_name': evidence_group.modified_by.first_name,
                'last_name': evidence_group.modified_by.last_name,
                'name': evidence_group.modified_by.name,
                'id': str(evidence_group.modified_by.pk),
            },
        }

    def test_restricted_user_can_get_evidence_group(self):
        """Test get evidence group by a restricted user."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        evidence_group = EvidenceGroupFactory(
            investment_project=investment_project
        )

        url = reverse('api-v3:investment:evidence-group:item', kwargs={
            'evidence_group_pk': evidence_group.pk,
            'project_pk': evidence_group.investment_project.pk,
        })
        user = create_test_user(
            permission_codenames=(
                EvidenceGroupPermission.read_associated_investmentproject,
            ),
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': str(evidence_group.pk),
            'investment_project': {
                'name': evidence_group.investment_project.name,
                'project_code': evidence_group.investment_project.project_code,
                'id': str(evidence_group.investment_project.pk),
            },
            'name': evidence_group.name,
            'created_on': format_date_or_datetime(evidence_group.created_on),
            'created_by': {
                'first_name': evidence_group.created_by.first_name,
                'last_name': evidence_group.created_by.last_name,
                'name': evidence_group.created_by.name,
                'id': str(evidence_group.created_by.pk),
            },
            'modified_on': format_date_or_datetime(evidence_group.modified_on),
            'modified_by': {
                'first_name': evidence_group.modified_by.first_name,
                'last_name': evidence_group.modified_by.last_name,
                'name': evidence_group.modified_by.name,
                'id': str(evidence_group.modified_by.pk),
            },
        }

    def test_restricted_user_cannot_get_non_associated_evidence_group(self):
        """Test get non associated evidence group by a restricted user."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator
        )
        evidence_group = EvidenceGroupFactory(
            investment_project=investment_project
        )

        url = reverse('api-v3:investment:evidence-group:item', kwargs={
            'evidence_group_pk': evidence_group.pk,
            'project_pk': evidence_group.investment_project.pk,
        })
        user = create_test_user(
            permission_codenames=(
                EvidenceGroupPermission.read_associated_investmentproject,
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
    def test_user_cannot_get_evidence_group_for_non_existent_project(self, permissions):
        """Test user cannot get evidence group by a non restricted user."""
        evidence_group = EvidenceGroupFactory()

        url = reverse('api-v3:investment:evidence-group:item', kwargs={
            'evidence_group_pk': evidence_group.pk,
            'project_pk': uuid.uuid4(),
        })
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

import datetime
import uuid
from unittest.mock import patch

import factory
import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.documents.models import Document, UploadStatus
from datahub.investment.project.proposition.constants import PropositionStatus
from datahub.investment.project.proposition.models import (
    Proposition,
    PropositionDocument,
    PropositionDocumentPermission,
    PropositionPermission,
)
from datahub.investment.project.proposition.test.factories import PropositionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory
from datahub.user_event_log.models import USER_EVENT_TYPES, UserEvent

NON_RESTRICTED_VIEW_PERMISSIONS = (
    (
        PropositionPermission.view_all,
        PropositionDocumentPermission.view_all,
    ),
    (
        PropositionPermission.view_all,
        PropositionDocumentPermission.view_all,
        PropositionPermission.view_associated,
        PropositionDocumentPermission.view_associated,
    ),
)


NON_RESTRICTED_ADD_PERMISSIONS = (
    (
        PropositionPermission.add_all,
        PropositionDocumentPermission.add_all,
    ),
    (
        PropositionPermission.add_all,
        PropositionDocumentPermission.add_all,
        PropositionPermission.add_associated,
        PropositionDocumentPermission.add_associated,
    ),
)


NON_RESTRICTED_CHANGE_PERMISSIONS = (
    (
        PropositionPermission.change_all,
        PropositionDocumentPermission.change_all,
    ),
    (
        PropositionPermission.change_all,
        PropositionDocumentPermission.change_all,
        PropositionPermission.change_associated,
        PropositionDocumentPermission.change_associated,
    ),
)


NON_RESTRICTED_DELETE_PERMISSIONS = (
    (
        PropositionPermission.delete_all,
        PropositionDocumentPermission.delete_all,
    ),
    (
        PropositionPermission.delete_all,
        PropositionDocumentPermission.delete_all,
        PropositionDocumentPermission.delete_associated,
    ),
)


class TestCreateProposition(APITestMixin):
    """Tests for the create proposition view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    def test_can_create_proposition(self, permissions):
        """Test creating proposition."""
        investment_project = InvestmentProjectFactory()

        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )

        adviser = create_test_user(
            permission_codenames=permissions,
        )
        api_client = self.create_api_client(user=adviser)

        response = api_client.post(
            url,
            {
                'name': 'My proposition.',
                'scope': 'Very broad scope.',
                'adviser': adviser.pk,
                'deadline': '2018-02-10',
            },
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
            'adviser': {
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
        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': uuid.uuid4(),
            },
        )

        adviser = create_test_user(
            permission_codenames=permissions,
        )
        api_client = self.create_api_client(user=adviser)

        response = api_client.post(
            url,
            {
                'name': 'My proposition.',
                'scope': 'Very broad scope.',
                'adviser': adviser.pk,
                'deadline': '2018-02-10',
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

    def test_restricted_user_can_create_associated_investment_project_proposition(self):
        """Test restricted user can create associated invesment project proposition."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(created_by=project_creator)

        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )

        adviser = create_test_user(
            permission_codenames=[PropositionPermission.add_associated],
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=adviser)
        response = api_client.post(
            url,
            {
                'name': 'My proposition.',
                'scope': 'Very broad scope.',
                'adviser': adviser.pk,
                'deadline': '2018-02-10',
            },
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
            'adviser': {
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

        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )

        adviser = create_test_user(
            permission_codenames=[PropositionPermission.add_associated],
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=adviser)
        response = api_client.post(
            url,
            {
                'name': 'My proposition.',
                'scope': 'Very broad scope.',
                'adviser': adviser.pk,
                'deadline': '2018-02-10',
            },
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response_data == {
            'detail': 'You do not have permission to perform this action.',
        }

    def test_cannot_created_with_fields_missing(self):
        """Test that proposition cannot be created without required fields."""
        investment_project = InvestmentProjectFactory()

        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'adviser': ['This field is required.'],
            'deadline': ['This field is required.'],
            'name': ['This field is required.'],
            'scope': ['This field is required.'],
        }


class TestUpdateProposition(APITestMixin):
    """Tests for the update proposition view."""

    @pytest.mark.parametrize(
        'method', ('put', 'patch'),
    )
    def test_cannot_update_collection(self, method):
        """Test cannot update proposition."""
        investment_project = InvestmentProjectFactory()
        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )
        response = getattr(self.api_client, method)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.parametrize(
        'method', ('put', 'patch'),
    )
    def test_cannot_update_item(self, method):
        """Test cannot update given proposition."""
        proposition = PropositionFactory()
        investment_project = InvestmentProjectFactory()
        url = reverse(
            'api-v3:investment:proposition:item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': investment_project.pk,
            },
        )
        response = getattr(self.api_client, method)(
            url,
            data={
                'name': 'hello!',
            },
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestListPropositions(APITestMixin):
    """Tests for the list propositions view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_non_restricted_user_can_list_propositions(self, permissions):
        """List of propositions by a non restricted user."""
        investment_project = InvestmentProjectFactory()

        PropositionFactory.create_batch(3)
        propositions = PropositionFactory.create_batch(
            3, investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in propositions}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_user_cannot_list_propositions_for_non_existent_investment_project(self, permissions):
        """Test user cannot list propositions for a non existent investment project."""
        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': uuid.uuid4(),
            },
        )

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
            created_by=project_creator,
        )
        propositions = PropositionFactory.create_batch(
            3, investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.view_associated,
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
            created_by=project_creator,
        )
        PropositionFactory.create_batch(
            3, investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.view_associated
            ),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_data = response.json()
        assert response_data == {
            'detail': 'You do not have permission to perform this action.',
        }

    def test_filtered_by_adviser(self):
        """List of propositions filtered by assigned adviser."""
        adviser = AdviserFactory()
        investment_project = InvestmentProjectFactory()

        PropositionFactory.create_batch(
            3, investment_project=investment_project,
        )
        propositions = PropositionFactory.create_batch(
            3,
            adviser=adviser,
            investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )
        response = self.api_client.get(
            url, {
                'adviser_id': adviser.id,
            },
        )

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
        ),
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

        url = reverse(
            'api-v3:investment:proposition:collection',
            kwargs={
                'project_pk': investment_project.pk,
            },
        )
        response = self.api_client.get(
            url, {
                'status': proposition_status,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['status'] == proposition_status


class TestGetProposition(APITestMixin):
    """Tests for get proposition view."""

    def test_fails_without_permissions(self, api_client):
        """Should return 401"""
        proposition = PropositionFactory()
        url = reverse(
            'api-v3:investment:proposition:item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_non_restricted_user_can_get_proposition(self, permissions):
        """Test get proposition by a non restricted user."""
        proposition = PropositionFactory()

        url = reverse(
            'api-v3:investment:proposition:item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
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
            'adviser': {
                'first_name': proposition.adviser.first_name,
                'last_name': proposition.adviser.last_name,
                'name': proposition.adviser.name,
                'id': str(proposition.adviser.pk),
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
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        user = create_test_user(
            permission_codenames=(
                PropositionPermission.view_associated,
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
            'adviser': {
                'first_name': proposition.adviser.first_name,
                'last_name': proposition.adviser.last_name,
                'name': proposition.adviser.name,
                'id': str(proposition.adviser.pk),
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
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        user = create_test_user(
            permission_codenames=(
                PropositionPermission.view_associated,
            ),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_data = response.json()
        assert response_data == {
            'detail': 'You do not have permission to perform this action.',
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_user_cannot_get_proposition_for_non_existent_project(self, permissions):
        """Test user cannot get proposition by a non restricted user."""
        proposition = PropositionFactory()

        url = reverse(
            'api-v3:investment:proposition:item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': uuid.uuid4(),
            },
        )
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}


class TestDeleteProposition(APITestMixin):
    """Tests for delete proposition view."""

    def test_fails_without_permissions(self, api_client):
        """Should return 401"""
        proposition = PropositionFactory()
        url = reverse(
            'api-v3:investment:proposition:item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_DELETE_PERMISSIONS)
    def test_non_restricted_user_cannot_delete_proposition(self, permissions):
        """Test that non restricted user cannot delete proposition."""
        proposition = PropositionFactory()

        url = reverse(
            'api-v3:investment:proposition:item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.json() == {'detail': 'Method is not allowed.'}


class TestCompleteProposition(APITestMixin):
    """Tests for the complete proposition view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    def test_non_restricted_user_can_complete_proposition(self, permissions):
        """Test completing proposition by non restricted user."""
        user = create_test_user(permission_codenames=permissions)
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )
        entity_document.document.mark_as_scanned(True, '')

        url = reverse(
            'api-v3:investment:proposition:complete',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.post(url)
        proposition.refresh_from_db()
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert proposition.modified_by == user
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
                'id': str(proposition.adviser.pk),
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
            'details': '',
            'modified_on': format_date_or_datetime(proposition.modified_on),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            },
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    def test_user_cannot_complete_proposition_for_non_existent_project(self, permissions):
        """Test user cannot complete proposition for non existent investment project."""
        user = create_test_user(permission_codenames=permissions)
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )
        entity_document.document.mark_as_scanned(True, '')
        url = reverse(
            'api-v3:investment:proposition:complete',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': uuid.uuid4(),
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

    def test_restricted_user_can_complete_proposition(self):
        """Test completing proposition by a restricted user."""
        project_creator = AdviserFactory()
        user = create_test_user(
            permission_codenames=(
                PropositionPermission.change_associated,
            ),
            dit_team=project_creator.dit_team,
        )
        investment_project = InvestmentProjectFactory(
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )
        entity_document.document.mark_as_scanned(True, '')

        url = reverse(
            'api-v3:investment:proposition:complete',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.post(url)
        proposition.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert proposition.modified_by == user
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
                'id': str(proposition.adviser.pk),
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
            'details': '',
            'modified_on': format_date_or_datetime(proposition.modified_on),
            'modified_by': {
                'first_name': proposition.modified_by.first_name,
                'last_name': proposition.modified_by.last_name,
                'name': proposition.modified_by.name,
                'id': str(proposition.modified_by.pk),
            },
        }

    def test_restricted_user_cannot_complete_non_associated_ip_proposition(self):
        """Test restricted user cannot complete non associated investment project proposition."""
        project_creator = AdviserFactory()
        user = create_test_user(
            permission_codenames=(
                PropositionPermission.change_associated,
            ),
            dit_team=TeamFactory(),
        )
        investment_project = InvestmentProjectFactory(
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )
        entity_document.document.mark_as_scanned(True, '')

        url = reverse(
            'api-v3:investment:proposition:complete',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        api_client = self.create_api_client(user=user)
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_data = response.json()
        assert response_data == {
            'detail': 'You do not have permission to perform this action.',
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
        user = create_test_user(
            permission_codenames=(
                PropositionPermission.change_all,
            ),
            dit_team=TeamFactory(),
        )
        proposition = PropositionFactory(
            status=proposition_status,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )
        entity_document.document.mark_as_scanned(True, '')
        url = reverse(
            'api-v3:investment:proposition:complete',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        api_client = self.create_api_client(user=user)
        response = api_client.post(url)
        response_data = response.json()
        assert response.status_code == status.HTTP_409_CONFLICT
        detail = f'The action cannot be performed in the current status {proposition_status}.'
        assert response_data['detail'] == detail

        proposition.refresh_from_db()
        assert proposition.status == proposition_status
        assert proposition.details == ''

    def test_cannot_complete_proposition_without_uploading_documents(self):
        """Test cannot complete proposition without uploading documents."""
        proposition = PropositionFactory()
        url = reverse(
            'api-v3:investment:proposition:complete',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        response = self.api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['non_field_errors'] == ['Proposition has no documents uploaded.']
        proposition.refresh_from_db()
        assert proposition.status == PropositionStatus.ongoing


class TestAbandonProposition(APITestMixin):
    """Tests for the abandon proposition view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    def test_non_restricted_user_can_abandon_proposition(self, permissions):
        """Test abandoning proposition by non restricted user."""
        proposition = PropositionFactory()

        url = reverse(
            'api-v3:investment:proposition:abandon',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'Not enough information.',
            },
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
            'adviser': {
                'first_name': proposition.adviser.first_name,
                'last_name': proposition.adviser.last_name,
                'name': proposition.adviser.name,
                'id': str(proposition.adviser.pk),
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

        url = reverse(
            'api-v3:investment:proposition:abandon',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': uuid.uuid4(),
            },
        )

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'Not enough information.',
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data == {'detail': 'Not found.'}

    def test_restricted_user_can_abandon_proposition(self):
        """Test abandoning proposition by restricted user."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:abandon',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.change_associated,
            ),
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'Not enough information.',
            },
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
            'adviser': {
                'first_name': proposition.adviser.first_name,
                'last_name': proposition.adviser.last_name,
                'name': proposition.adviser.name,
                'id': str(proposition.adviser.pk),
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
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:abandon',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )

        user = create_test_user(
            permission_codenames=(
                PropositionPermission.change_associated,
            ),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            url,
            {
                'details': 'Not enough information.',
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_data = response.json()
        assert response_data == {
            'detail': 'You do not have permission to perform this action.',
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
            status=proposition_status,
        )
        url = reverse(
            'api-v3:investment:proposition:abandon',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        response = self.api_client.post(
            url,
            {
                'details': 'Too many cats.',
            },
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
        url = reverse(
            'api-v3:investment:proposition:abandon',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        response = self.api_client.post(
            url,
            {
                'details': '',
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['details'] == ['This field may not be blank.']
        proposition.refresh_from_db()
        assert proposition.status == PropositionStatus.ongoing


@pytest.mark.parametrize('http_method', ('get', 'post'))
class TestPropositionDocumentCollectionView404Handling(APITestMixin):
    """Tests for 404-handling in the proposition document collection view."""

    def test_returns_404_for_non_existent_project(self, http_method):
        """Test that a 404 is returned if an non-existent project is specified."""
        proposition = PropositionFactory()

        url = reverse(
            'api-v3:investment:proposition:document-collection',
            kwargs={
                'project_pk': uuid.uuid4(),
                'proposition_pk': proposition.pk,
            },
        )
        response = self.api_client.generic(http_method, url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_for_non_existent_proposition(self, http_method):
        """Test that a 404 is returned if an non-existent proposition is specified."""
        project = InvestmentProjectFactory()

        url = reverse(
            'api-v3:investment:proposition:document-collection',
            kwargs={
                'project_pk': project.pk,
                'proposition_pk': uuid.uuid4(),
            },
        )
        response = self.api_client.generic(http_method, url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_for_mismatched_proposition_and_project(self, http_method):
        """Test that a 404 is returned if an unrelated project and proposition are specified."""
        proposition = PropositionFactory()
        project = InvestmentProjectFactory()

        url = reverse(
            'api-v3:investment:proposition:document-collection',
            kwargs={
                'project_pk': project.pk,
                'proposition_pk': proposition.pk,
            },
        )
        response = self.api_client.generic(http_method, url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    'urlname,http_method',
    (
        ('api-v3:investment:proposition:document-item', 'get'),
        ('api-v3:investment:proposition:document-item', 'delete'),
        ('api-v3:investment:proposition:document-item-callback', 'post'),
        ('api-v3:investment:proposition:document-item-download', 'get'),
    ),
)
class TestPropositionDocumentItemViews404Handling(APITestMixin):
    """Tests for 404-handling in all proposition document item views."""

    def test_returns_404_for_non_existent_project(self, urlname, http_method):
        """Test that a 404 is returned if a non-existent project is specified."""
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=self.user,
        )

        url = reverse(
            urlname,
            kwargs={
                'project_pk': uuid.uuid4(),
                'proposition_pk': proposition.pk,
                'entity_document_pk': entity_document.pk,
            },
        )
        response = self.api_client.generic(http_method, url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_for_non_existent_proposition(self, urlname, http_method):
        """Test that a 404 is returned if a non-existent proposition is specified."""
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=self.user,
        )

        url = reverse(
            urlname,
            kwargs={
                'project_pk': proposition.investment_project.pk,
                'proposition_pk': uuid.uuid4(),
                'entity_document_pk': entity_document.pk,
            },
        )
        response = self.api_client.generic(http_method, url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_for_non_existent_document(self, urlname, http_method):
        """Test that a 404 is returned if a non-existent document is specified."""
        proposition = PropositionFactory()

        url = reverse(
            urlname,
            kwargs={
                'project_pk': proposition.investment_project.pk,
                'proposition_pk': proposition.pk,
                'entity_document_pk': uuid.uuid4(),
            },
        )
        response = self.api_client.generic(http_method, url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_for_unrelated_project(self, urlname, http_method):
        """Test that a 404 is returned if an unrelated project is specified."""
        unrelated_project = InvestmentProjectFactory()
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=self.user,
        )

        url = reverse(
            urlname,
            kwargs={
                'project_pk': unrelated_project.pk,
                'proposition_pk': proposition.pk,
                'entity_document_pk': entity_document.pk,
            },
        )
        response = self.api_client.generic(http_method, url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_for_unrelated_proposition(self, urlname, http_method):
        """Test that a 404 is returned if an unrelated proposition is specified."""
        proposition = PropositionFactory()
        unrelated_proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=self.user,
        )

        url = reverse(
            urlname,
            kwargs={
                'project_pk': proposition.investment_project.pk,
                'proposition_pk': unrelated_proposition.pk,
                'entity_document_pk': entity_document.pk,
            },
        )
        response = self.api_client.generic(http_method, url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPropositionDocumentViews(APITestMixin):
    """Tests for the proposition document views."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    @patch.object(Document, 'get_signed_upload_url')
    def test_document_creation(self, get_signed_upload_url_mock, permissions):
        """Test document creation."""
        get_signed_upload_url_mock.return_value = 'http://document-about-ocelots'

        proposition = PropositionFactory()

        url = reverse(
            'api-v3:investment:proposition:document-collection',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        response = api_client.post(
            url,
            data={
                'original_filename': 'test.txt',
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.data

        entity_document = PropositionDocument.objects.get(pk=response_data['id'])
        assert entity_document.original_filename == 'test.txt'
        assert entity_document.proposition.pk == proposition.pk

        assert response_data == {
            'id': str(entity_document.pk),
            'av_clean': None,
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name,
            },
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document.proposition, entity_document),
            'status': UploadStatus.NOT_VIRUS_SCANNED,
            'signed_upload_url': 'http://document-about-ocelots',
            'created_on': format_date_or_datetime(entity_document.created_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }

    @patch.object(Document, 'get_signed_upload_url')
    def test_restricted_user_can_create_associated_document(self, get_signed_upload_url_mock):
        """Test that restricted user can create associated document."""
        get_signed_upload_url_mock.return_value = 'http://document-about-ocelots'

        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.add_associated,),
            dit_team=TeamFactory(),
        )
        investment_project = InvestmentProjectFactory(
            created_by=user,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:document-collection',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )

        api_client = self.create_api_client(user=user)

        response = api_client.post(
            url,
            data={
                'original_filename': 'test.txt',
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.data

        entity_document = PropositionDocument.objects.get(pk=response_data['id'])
        assert entity_document.original_filename == 'test.txt'
        assert entity_document.proposition.pk == proposition.pk

        assert response_data == {
            'id': str(entity_document.pk),
            'av_clean': None,
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name,
            },
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document.proposition, entity_document),
            'status': UploadStatus.NOT_VIRUS_SCANNED,
            'signed_upload_url': 'http://document-about-ocelots',
            'created_on': format_date_or_datetime(entity_document.created_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }

    def test_restricted_user_cannot_create_non_associated_documents(self):
        """Test that restricted user cannot create non associated document."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )

        url = reverse(
            'api-v3:investment:proposition:document-collection',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )

        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.add_associated,),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)

        response = api_client.post(
            url,
            data={
                'original_filename': 'test.txt',
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            'detail': 'You do not have permission to perform this action.',
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_documents_list(self, permissions):
        """Tests list endpoint."""
        user = create_test_user(permission_codenames=permissions)
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )
        entity_document.document.mark_as_scanned(True, '')
        # document that is pending to be deleted, shouldn't be in the list
        entity_document_to_be_deleted = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test2.txt',
            created_by=user,
        )
        entity_document_to_be_deleted.document.mark_deletion_pending()

        url = reverse(
            'api-v3:investment:proposition:document-collection',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.data
        assert response_data['count'] == 1
        assert len(response_data['results']) == 1
        assert response_data['results'][0] == {
            'id': str(entity_document.pk),
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name,
            },
            'av_clean': True,
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document.proposition, entity_document),
            'status': UploadStatus.VIRUS_SCANNED,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }

    def test_restricted_user_can_list_associated_documents(self):
        """Test that restricted user can list associated documents."""
        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.view_associated,),
            dit_team=TeamFactory(),
        )
        investment_project = InvestmentProjectFactory(
            created_by=user,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )
        entity_document.document.mark_as_scanned(True, '')
        # document that is pending to be deleted, shouldn't be in the list
        entity_document_to_be_deleted = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test2.txt',
            created_by=user,
        )
        entity_document_to_be_deleted.document.mark_deletion_pending()

        url = reverse(
            'api-v3:investment:proposition:document-collection',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.data
        assert response_data['count'] == 1
        assert len(response_data['results']) == 1
        assert response_data['results'][0] == {
            'id': str(entity_document.pk),
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name,
            },
            'av_clean': True,
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document.proposition, entity_document),
            'status': UploadStatus.VIRUS_SCANNED,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }

    def test_restricted_user_cannot_list_non_associated_documents(self):
        """Tests that restricted user cannot list non associated documents."""
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=project_creator,
        )
        entity_document.document.mark_as_scanned(True, '')

        url = reverse(
            'api-v3:investment:proposition:document-collection',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
            },
        )
        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.view_associated,),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            'detail': 'You do not have permission to perform this action.',
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_document_retrieval(self, permissions):
        """Tests retrieval of individual document."""
        user = create_test_user(permission_codenames=permissions)
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        api_client = self.create_api_client(user=user)

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'id': str(entity_document.pk),
            'av_clean': None,
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name,
            },
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document.proposition, entity_document),
            'status': UploadStatus.NOT_VIRUS_SCANNED,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }

    def test_restricted_user_can_retrieve_associated_document(self):
        """Test that restricted user can retrieve individual associated document."""
        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.view_associated,),
            dit_team=TeamFactory(),
        )
        investment_project = InvestmentProjectFactory(
            created_by=user,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'id': str(entity_document.pk),
            'av_clean': None,
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name,
            },
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document.proposition, entity_document),
            'status': UploadStatus.NOT_VIRUS_SCANNED,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }

    def test_restricted_user_cannot_retrieve_non_associated_document(self):
        """Test that restricted user cannot retrieve individual non associated document."""
        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.view_associated,),
            dit_team=TeamFactory(),
        )
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=project_creator,
        )
        entity_document.document.mark_as_scanned(True, '')

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            'detail': 'You do not have permission to perform this action.',
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_document_with_deletion_pending_retrieval(self, permissions):
        """Tests retrieval of individual document that is pending deletion."""
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk, original_filename='test.txt',
        )
        entity_document.document.mark_deletion_pending()

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'av_clean,expected_status', (
            (True, status.HTTP_200_OK),
            (False, status.HTTP_403_FORBIDDEN),
        ),
    )
    @patch('datahub.documents.models.sign_s3_url')
    def test_document_download(self, sign_s3_url, av_clean, expected_status):
        """Tests download of individual document."""
        sign_s3_url.return_value = 'http://what'

        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.view_all,),
        )
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )
        entity_document.document.mark_as_scanned(av_clean, '')

        url = reverse(
            'api-v3:investment:proposition:document-item-download',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.get(url)
        assert response.status_code == expected_status
        if response.status_code == status.HTTP_200_OK:
            assert response.data == {
                'id': str(entity_document.pk),
                'av_clean': True,
                'created_by': {
                    'id': str(entity_document.created_by.pk),
                    'first_name': entity_document.created_by.first_name,
                    'last_name': entity_document.created_by.last_name,
                    'name': entity_document.created_by.name,
                },
                'original_filename': 'test.txt',
                'url': _get_document_url(entity_document.proposition, entity_document),
                'status': UploadStatus.VIRUS_SCANNED,
                'document_url': 'http://what',
                'created_on': format_date_or_datetime(entity_document.created_on),
                'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
            }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_document_download_when_not_scanned(self, permissions):
        """Tests download of individual document when not yet virus scanned."""
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk, original_filename='test.txt',
        )

        url = reverse(
            'api-v3:investment:proposition:document-item-download',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        response = api_client.get(url)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    @patch('datahub.documents.tasks.virus_scan_document.apply_async')
    def test_document_upload_schedule_virus_scan(
        self,
        virus_scan_document_apply_async,
        permissions,
    ):
        """Tests scheduling virus scan after upload completion.

        Checks that a virus scan of the document was scheduled. Virus scanning is
        tested separately in the documents app.
        """
        user = create_test_user(permission_codenames=permissions)
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )

        url = reverse(
            'api-v3:investment:proposition:document-item-callback',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        entity_document.document.refresh_from_db()

        assert response.data == {
            'id': str(entity_document.pk),
            'av_clean': None,
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name,
            },

            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document.proposition, entity_document),
            'status': UploadStatus.VIRUS_SCANNING_SCHEDULED,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }
        virus_scan_document_apply_async.assert_called_once_with(
            args=(str(entity_document.document.pk), ),
        )

    @patch('datahub.documents.tasks.virus_scan_document.apply_async')
    def test_restricted_user_can_schedule_virus_scan_for_associated_document(
        self,
        virus_scan_document_apply_async,
    ):
        """
        Test that restricted user can schedule a virus scan for associated document.
        """
        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.change_associated,),
            dit_team=TeamFactory(),
        )
        investment_project = InvestmentProjectFactory(
            created_by=user,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )

        url = reverse(
            'api-v3:investment:proposition:document-item-callback',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        entity_document.document.refresh_from_db()

        assert response.data == {
            'id': str(entity_document.pk),
            'av_clean': None,
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name,
            },

            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document.proposition, entity_document),
            'status': UploadStatus.VIRUS_SCANNING_SCHEDULED,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }
        virus_scan_document_apply_async.assert_called_once_with(
            args=(str(entity_document.document.pk), ),
        )

    def test_restricted_user_cannot_schedule_virus_scan_for_non_associated_document(self):
        """Test that restricted user cannot schedule a virus scan for non associated document."""
        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.change_associated,),
            dit_team=TeamFactory(),
        )
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=project_creator,
        )

        url = reverse(
            'api-v3:investment:proposition:document-item-callback',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            'detail': 'You do not have permission to perform this action.',
        }

        entity_document.document.refresh_from_db()
        assert entity_document.document.status == UploadStatus.NOT_VIRUS_SCANNED

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_DELETE_PERMISSIONS)
    @patch('datahub.documents.tasks.delete_document.apply_async')
    def test_document_delete(self, delete_document, permissions):
        """Tests document deletion."""
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk, original_filename='test.txt',
        )
        document = entity_document.document
        document.mark_scan_scheduled()
        document.mark_as_scanned(True, 'reason')

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        document_pk = entity_document.document.pk

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        delete_document.assert_called_once_with(args=(document_pk, ))

    @patch('datahub.documents.tasks.delete_document.apply_async')
    def test_restricted_user_can_delete_associated_document(self, delete_document):
        """Test that restricted user can delete associated document."""
        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.delete_associated,),
            dit_team=TeamFactory(),
        )
        investment_project = InvestmentProjectFactory(
            created_by=user,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=user,
        )
        document = entity_document.document
        document.mark_scan_scheduled()
        document.mark_as_scanned(True, 'reason')

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        document_pk = entity_document.document.pk

        api_client = self.create_api_client(user=user)
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        delete_document.assert_called_once_with(args=(document_pk, ))

    @patch('datahub.documents.tasks.delete_document.apply_async')
    def test_restricted_user_cannot_delete_non_associated_document(self, delete_document):
        """Test that restricted user cannot delete non associated document."""
        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.delete_associated,),
            dit_team=TeamFactory(),
        )
        project_creator = AdviserFactory()
        investment_project = InvestmentProjectFactory(
            created_by=project_creator,
        )
        proposition = PropositionFactory(
            investment_project=investment_project,
        )
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk,
            original_filename='test.txt',
            created_by=project_creator,
        )
        document = entity_document.document
        document.mark_scan_scheduled()
        document.mark_as_scanned(True, 'reason')

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            'detail': 'You do not have permission to perform this action.',
        }

        entity_document.document.refresh_from_db()
        assert entity_document.document.status == UploadStatus.VIRUS_SCANNED
        assert delete_document.called is False

    @patch('datahub.documents.tasks.delete_document.apply_async')
    def test_document_delete_without_permission(self, delete_document):
        """Tests user can't delete document without permissions."""
        user = create_test_user(
            permission_codenames=(),
            dit_team=TeamFactory(),
        )
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk, original_filename='test.txt',
        )
        entity_document.document.mark_scan_scheduled()
        entity_document.document.mark_as_scanned(True, 'reason')

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )
        api_client = self.create_api_client(user=user)
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert delete_document.called is False

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_DELETE_PERMISSIONS)
    @patch('datahub.documents.tasks.delete_document.apply_async')
    def test_document_delete_creates_user_event_log(self, delete_document, permissions):
        """Tests document deletion creates user event log."""
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk, original_filename='test.txt',
        )
        document = entity_document.document
        document.mark_scan_scheduled()
        document.mark_as_scanned(True, 'reason')

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        document_pk = entity_document.document.pk

        expected_user_event_data = {
            'id': str(entity_document.pk),
            'url': entity_document.url,
            'status': entity_document.document.status,
            'av_clean': entity_document.document.av_clean,
            'created_by': None,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
            'original_filename': entity_document.original_filename,
            'proposition_id': str(entity_document.proposition_id),
        }

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        frozen_time = datetime.datetime(2018, 1, 2, 12, 30, 50, tzinfo=utc)
        with freeze_time(frozen_time):
            response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        delete_document.assert_called_once_with(args=(document_pk, ))

        assert UserEvent.objects.count() == 1

        user_event = UserEvent.objects.first()
        assert user_event.adviser == user
        assert user_event.type == USER_EVENT_TYPES.proposition_document_delete
        assert user_event.timestamp == frozen_time
        assert user_event.api_url_path == url
        assert user_event.data == expected_user_event_data

    @patch.object(Document, 'mark_deletion_pending')
    def test_document_delete_failure_wont_create_user_event_log(self, mark_deletion_pending):
        """Tests document deletion failure won't create user event log."""
        mark_deletion_pending.side_effect = Exception('No way!')
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk, original_filename='test.txt',
        )
        document = entity_document.document
        document.mark_scan_scheduled()
        document.mark_as_scanned(True, 'reason')

        url = reverse(
            'api-v3:investment:proposition:document-item',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )
        user = create_test_user(
            permission_codenames=(PropositionDocumentPermission.delete_all,),
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=user)
        with pytest.raises(Exception):
            api_client.delete(url)

        assert UserEvent.objects.count() == 0

    def test_document_upload_status_no_status_without_permission(self):
        """Tests user without permission can't call upload status endpoint."""
        user = create_test_user(
            permission_codenames=(),
            dit_team=TeamFactory(),
        )
        proposition = PropositionFactory()
        entity_document = PropositionDocument.objects.create(
            proposition_id=proposition.pk, original_filename='test.txt',
        )

        url = reverse(
            'api-v3:investment:proposition:document-item-callback',
            kwargs={
                'proposition_pk': proposition.pk,
                'project_pk': proposition.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            },
        )

        api_client = self.create_api_client(user=user)
        response = api_client.post(url, data={})
        assert response.status_code == status.HTTP_403_FORBIDDEN


def _get_document_url(proposition, entity_document):
    return reverse(
        'api-v3:investment:proposition:document-item-download',
        kwargs={
            'proposition_pk': proposition.pk,
            'project_pk': proposition.investment_project.pk,
            'entity_document_pk': entity_document.pk,
        },
    )

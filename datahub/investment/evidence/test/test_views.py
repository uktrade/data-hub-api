from operator import attrgetter
from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import TeamFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.documents.models import Document, UPLOAD_STATUSES
from datahub.investment.test.factories import InvestmentProjectFactory
from .factories import EvidenceTagFactory
from .utils import create_evidence_document
from ..models import EvidenceDocument, EvidenceDocumentPermission

pytestmark = pytest.mark.django_db

VIEW_PERMISSIONS = (
    (
        (
            EvidenceDocumentPermission.view_all,
        ),
        False,  # associated to investment project?
        True,   # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.view_all,
            EvidenceDocumentPermission.view_associated_investmentproject,
        ),
        False,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.view_associated_investmentproject,
        ),
        True,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.view_associated_investmentproject,
        ),
        False,  # associated to investment project?
        False,  # should be allowed?
    ),
)


ADD_PERMISSIONS = (
    (
        (
            EvidenceDocumentPermission.add_all,
        ),
        False,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.add_all,
            EvidenceDocumentPermission.add_associated_investmentproject,
        ),
        False,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.add_associated_investmentproject,
        ),
        True,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.add_associated_investmentproject,
        ),
        False,  # associated to investment project?
        False,  # should be allowed?
    ),
)


CHANGE_PERMISSIONS = (
    (
        (
            EvidenceDocumentPermission.change_all,
        ),
        False,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.change_all,
            EvidenceDocumentPermission.change_associated_investmentproject,
        ),
        False,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.change_associated_investmentproject,
        ),
        True,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.change_associated_investmentproject,
        ),
        False,  # associated to investment project?
        False,  # should be allowed?
    ),
)


DELETE_PERMISSIONS = (
    (
        (
            EvidenceDocumentPermission.delete_all,
        ),
        False,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.delete_all,
            EvidenceDocumentPermission.delete_associated_investmentproject,
        ),
        False,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.delete_associated_investmentproject,
        ),
        True,  # associated to investment project?
        True,  # should be allowed?
    ),
    (
        (
            EvidenceDocumentPermission.delete_associated_investmentproject,
        ),
        False,  # associated to investment project?
        False,  # should be allowed?
    ),
)


class TestEvidenceDocumentViews(APITestMixin):
    """Tests for the evidence document views."""

    @pytest.mark.parametrize('permissions,associated,allowed', ADD_PERMISSIONS)
    @patch.object(Document, 'get_signed_upload_url')
    def test_document_creation(self, get_signed_upload_url_mock, permissions, associated, allowed):
        """Test document creation."""
        get_signed_upload_url_mock.return_value = 'http://document-about-ocelots'
        user = create_test_user(permission_codenames=permissions, dit_team=TeamFactory())

        evidence_tags = EvidenceTagFactory.create_batch(2)
        investment_project = InvestmentProjectFactory()
        if associated:
            investment_project.created_by.dit_team = user.dit_team
            investment_project.created_by.save()

        url = reverse('api-v3:investment:evidence-document:document-collection', kwargs={
            'project_pk': investment_project.pk,
        })

        api_client = self.create_api_client(user=user)
        response = api_client.post(url, format='json', data={
            'original_filename': 'test.txt',
            'tags': [tag.pk for tag in evidence_tags],
        })
        response_data = response.json()

        if not allowed:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response_data == {
                'detail': 'You do not have permission to perform this action.'
            }
            return

        assert response.status_code == status.HTTP_201_CREATED

        entity_document = EvidenceDocument.objects.get(pk=response_data['id'])
        assert entity_document.original_filename == 'test.txt'
        assert entity_document.investment_project.pk == investment_project.pk

        assert response_data == {
            'id': str(entity_document.pk),
            'av_clean': None,
            'comment': entity_document.comment,
            'investment_project': {
                'name': entity_document.investment_project.name,
                'project_code': entity_document.investment_project.project_code,
                'id': str(entity_document.investment_project.pk),
            },
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name
            },
            'modified_by': None,
            'tags': [
                {'id': str(tag.id), 'name': tag.name}
                for tag in sorted(entity_document.tags.all(), key=attrgetter('name'))
            ],
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document),
            'status': UPLOAD_STATUSES.not_virus_scanned,
            'signed_upload_url': 'http://document-about-ocelots',
            'created_on': format_date_or_datetime(entity_document.created_on),
            'modified_on': format_date_or_datetime(entity_document.modified_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }

    @pytest.mark.parametrize('permissions,associated,allowed', VIEW_PERMISSIONS)
    def test_documents_list(self, permissions, associated, allowed):
        """Tests list endpoint."""
        user = create_test_user(permission_codenames=permissions, dit_team=TeamFactory())
        entity_document = create_evidence_document(user, associated=associated)
        entity_document.document.mark_as_scanned(True, '')
        # document that is pending to be deleted, shouldn't be in the list
        investment_project = entity_document.investment_project
        entity_document_to_be_deleted = create_evidence_document(user, investment_project)
        entity_document_to_be_deleted.document.mark_deletion_pending()

        url = reverse(
            'api-v3:investment:evidence-document:document-collection',
            kwargs={
                'project_pk': investment_project.pk,
            }
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        response_data = response.json()

        if not allowed:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response_data == {
                'detail': 'You do not have permission to perform this action.'
            }
            return

        assert response.status_code == status.HTTP_200_OK
        assert response_data['count'] == 1
        assert len(response_data['results']) == 1
        assert response_data['results'][0] == {
            'id': str(entity_document.pk),
            'av_clean': True,
            'comment': entity_document.comment,
            'investment_project': {
                'name': entity_document.investment_project.name,
                'project_code': entity_document.investment_project.project_code,
                'id': str(entity_document.investment_project.pk),
            },
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name
            },
            'modified_by': None,
            'tags': [
                {'id': str(tag.id), 'name': tag.name}
                for tag in sorted(entity_document.tags.all(), key=attrgetter('name'))
            ],
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document),
            'status': UPLOAD_STATUSES.virus_scanned,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'modified_on': format_date_or_datetime(entity_document.modified_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }

    @pytest.mark.parametrize('permissions,associated,allowed', VIEW_PERMISSIONS)
    def test_document_retrieval(self, permissions, associated, allowed):
        """Tests retrieval of individual document."""
        user = create_test_user(permission_codenames=permissions, dit_team=TeamFactory())
        entity_document = create_evidence_document(user, associated=associated)

        url = reverse(
            'api-v3:investment:evidence-document:document-item',
            kwargs={
                'project_pk': entity_document.investment_project.pk,
                'entity_document_pk': entity_document.pk
            }
        )

        api_client = self.create_api_client(user=user)
        response = api_client.get(url)
        response_data = response.json()

        if not allowed:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response_data == {
                'detail': 'You do not have permission to perform this action.'
            }
            return

        assert response.status_code == status.HTTP_200_OK
        assert response_data == {
            'id': str(entity_document.pk),
            'av_clean': None,
            'comment': entity_document.comment,
            'investment_project': {
                'name': entity_document.investment_project.name,
                'project_code': entity_document.investment_project.project_code,
                'id': str(entity_document.investment_project.pk),
            },
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name
            },
            'modified_by': None,
            'tags': [
                {'id': str(tag.id), 'name': tag.name}
                for tag in sorted(entity_document.tags.all(), key=attrgetter('name'))
            ],
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document),
            'status': UPLOAD_STATUSES.not_virus_scanned,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'modified_on': format_date_or_datetime(entity_document.modified_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }

    @pytest.mark.parametrize('permissions,associated,allowed', VIEW_PERMISSIONS)
    def test_document_with_deletion_pending_retrieval(self, permissions, associated, allowed):
        """Tests retrieval of individual document that is pending deletion."""
        user = create_test_user(permission_codenames=permissions, dit_team=TeamFactory())

        entity_document = create_evidence_document(user, associated=associated)
        entity_document.document.mark_deletion_pending()

        url = reverse(
            'api-v3:investment:evidence-document:document-item',
            kwargs={
                'project_pk': entity_document.investment_project.pk,
                'entity_document_pk': entity_document.pk
            }
        )

        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        if not allowed:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.json() == {
                'detail': 'You do not have permission to perform this action.'
            }
            return

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'av_clean,expected_status', (
            (True, status.HTTP_200_OK),
            (False, status.HTTP_403_FORBIDDEN,)
        )
    )
    @pytest.mark.parametrize('permissions,associated,allowed', VIEW_PERMISSIONS)
    @patch('datahub.documents.models.sign_s3_url')
    def test_document_download(
        self, sign_s3_url, permissions, associated, allowed, av_clean, expected_status
    ):
        """Tests download of individual document."""
        sign_s3_url.return_value = 'http://what'

        user = create_test_user(permission_codenames=permissions, dit_team=TeamFactory())
        entity_document = create_evidence_document(user, associated=associated)
        entity_document.document.mark_as_scanned(av_clean, '')

        url = reverse(
            'api-v3:investment:evidence-document:document-item-download',
            kwargs={
                'project_pk': entity_document.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            }
        )

        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        response_data = response.json()

        if not allowed:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response_data == {
                'detail': 'You do not have permission to perform this action.'
            }
            return

        assert response.status_code == expected_status
        if response.status_code == status.HTTP_200_OK:
            assert response_data == {
                'id': str(entity_document.pk),
                'av_clean': True,
                'comment': entity_document.comment,
                'investment_project': {
                    'name': entity_document.investment_project.name,
                    'project_code': entity_document.investment_project.project_code,
                    'id': str(entity_document.investment_project.pk),
                },
                'created_by': {
                    'id': str(entity_document.created_by.pk),
                    'first_name': entity_document.created_by.first_name,
                    'last_name': entity_document.created_by.last_name,
                    'name': entity_document.created_by.name
                },
                'modified_by': None,
                'tags': [
                    {'id': str(tag.id), 'name': tag.name}
                    for tag in sorted(entity_document.tags.all(), key=attrgetter('name'))
                ],
                'original_filename': 'test.txt',
                'url': _get_document_url(entity_document),
                'status': UPLOAD_STATUSES.virus_scanned,
                'created_on': format_date_or_datetime(entity_document.created_on),
                'modified_on': format_date_or_datetime(entity_document.modified_on),
                'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
                'document_url': 'http://what',
            }

    @pytest.mark.parametrize('permissions,associated,allowed', VIEW_PERMISSIONS)
    def test_document_download_when_not_scanned(self, permissions, associated, allowed):
        """Tests download of individual document when not yet virus scanned."""
        user = create_test_user(permission_codenames=permissions, dit_team=TeamFactory())
        entity_document = create_evidence_document(user, associated=associated)

        url = reverse(
            'api-v3:investment:evidence-document:document-item-download',
            kwargs={
                'project_pk': entity_document.investment_project.pk,
                'entity_document_pk': entity_document.pk,
            }
        )

        api_client = self.create_api_client(user=user)
        response = api_client.get(url)
        response_data = response.json()

        if not allowed:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response_data == {
                'detail': 'You do not have permission to perform this action.'
            }
            return

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.parametrize('permissions,associated,allowed', CHANGE_PERMISSIONS)
    @patch('datahub.documents.tasks.virus_scan_document.apply_async')
    def test_document_upload_schedule_virus_scan(
        self,
        virus_scan_document_apply_async,
        permissions,
        associated,
        allowed
    ):
        """Tests scheduling virus scan after upload completion.

        Checks that a virus scan of the document was scheduled. Virus scanning is
        tested separately in the documents app.
        """
        user = create_test_user(permission_codenames=permissions, dit_team=TeamFactory())
        entity_document = create_evidence_document(user, associated=associated)

        url = reverse(
            'api-v3:investment:evidence-document:document-item-callback',
            kwargs={
                'project_pk': entity_document.investment_project.pk,
                'entity_document_pk': entity_document.pk
            }
        )

        api_client = self.create_api_client(user=user)
        response = api_client.post(url, format='json')
        response_data = response.json()

        if not allowed:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response_data == {
                'detail': 'You do not have permission to perform this action.'
            }
            return

        assert response.status_code == status.HTTP_200_OK
        entity_document.document.refresh_from_db()
        assert response_data == {
            'id': str(entity_document.pk),
            'av_clean': None,
            'comment': entity_document.comment,
            'investment_project': {
                'name': entity_document.investment_project.name,
                'project_code': entity_document.investment_project.project_code,
                'id': str(entity_document.investment_project.pk),
            },
            'created_by': {
                'id': str(entity_document.created_by.pk),
                'first_name': entity_document.created_by.first_name,
                'last_name': entity_document.created_by.last_name,
                'name': entity_document.created_by.name
            },
            'modified_by': None,
            'tags': [
                {'id': str(tag.id), 'name': tag.name}
                for tag in sorted(entity_document.tags.all(), key=attrgetter('name'))
            ],
            'original_filename': 'test.txt',
            'url': _get_document_url(entity_document),
            'status': UPLOAD_STATUSES.virus_scanning_scheduled,
            'created_on': format_date_or_datetime(entity_document.created_on),
            'modified_on': format_date_or_datetime(entity_document.modified_on),
            'uploaded_on': format_date_or_datetime(entity_document.document.uploaded_on),
        }
        virus_scan_document_apply_async.assert_called_once_with(
            args=(str(entity_document.document.pk), )
        )

    @pytest.mark.parametrize('permissions,associated,allowed', DELETE_PERMISSIONS)
    @patch('datahub.documents.tasks.delete_document.apply_async')
    def test_document_delete(self, delete_document, permissions, associated, allowed):
        """Tests document deletion."""
        user = create_test_user(permission_codenames=permissions, dit_team=TeamFactory())
        entity_document = create_evidence_document(user, associated=associated)
        document = entity_document.document
        document.mark_scan_scheduled()
        document.mark_as_scanned(True, 'reason')

        url = reverse(
            'api-v3:investment:evidence-document:document-item',
            kwargs={
                'project_pk': entity_document.investment_project.pk,
                'entity_document_pk': entity_document.pk
            }
        )

        document_pk = entity_document.document.pk

        api_client = self.create_api_client(user=user)
        response = api_client.delete(url)

        if not allowed:
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.json() == {
                'detail': 'You do not have permission to perform this action.'
            }
            return

        assert response.status_code == status.HTTP_204_NO_CONTENT
        delete_document.assert_called_once_with(args=(document_pk, ))

    @patch('datahub.documents.tasks.delete_document.apply_async')
    def test_document_delete_without_permission(self, delete_document):
        """Tests user can't delete document without permissions."""
        entity_document = create_evidence_document()
        entity_document.document.mark_scan_scheduled()
        entity_document.document.mark_as_scanned(True, 'reason')

        url = reverse(
            'api-v3:investment:evidence-document:document-item',
            kwargs={
                'project_pk': entity_document.investment_project.pk,
                'entity_document_pk': entity_document.pk
            }
        )
        user = create_test_user(permission_codenames=[], dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert delete_document.called is False

    def test_document_upload_status_no_status_without_permission(self):
        """Tests user without permission can't call upload status endpoint."""
        entity_document = create_evidence_document()

        url = reverse(
            'api-v3:investment:evidence-document:document-item-callback',
            kwargs={
                'project_pk': entity_document.investment_project.pk,
                'entity_document_pk': entity_document.pk
            }
        )

        user = create_test_user(permission_codenames=[], dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        response = api_client.post(url, format='json', data={})
        assert response.status_code == status.HTTP_403_FORBIDDEN


def _get_document_url(entity_document):
    return reverse(
        'api-v3:investment:evidence-document:document-item-download',
        kwargs={
            'project_pk': entity_document.investment_project.pk,
            'entity_document_pk': entity_document.pk,
        }
    )

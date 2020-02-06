"""Tests for generic document views."""

from unittest.mock import patch

import pytest
from django.test.utils import override_settings
from django.utils.timezone import now
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.documents.models import Document, UploadStatus
from datahub.documents.test.my_entity_document.models import MyEntityDocument


@pytest.fixture
def test_urls():  # noqa: D403
    """pytest fixture to override the ROOT_URLCONF with test views."""
    with override_settings(ROOT_URLCONF='datahub.documents.test.my_entity_document.urls'):
        yield


class TestDocumentViews(APITestMixin):
    """Tests for the document views."""

    def test_documents_list(self, test_urls):
        """Tests list endpoint."""
        entity_document = MyEntityDocument.objects.create(
            my_field='cats have five toes',
            original_filename='test.txt',
        )
        # document that is pending to be deleted, shouldn't be in the list
        entity_document_to_be_deleted = MyEntityDocument.objects.create(
            my_field='now what?',
            original_filename='test1.txt',
        )
        entity_document_to_be_deleted.document.mark_deletion_pending()

        url = reverse('test-document-collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.data
        assert response_data['count'] == 1
        assert len(response_data['results']) == 1
        assert response_data['results'][0] == {
            'id': str(entity_document.pk),
            'my_field': 'cats have five toes',
            'original_filename': 'test.txt',
            'url': entity_document.url,
            'status': 'not_virus_scanned',
        }

    @patch.object(Document, 'get_signed_upload_url')
    def test_document_creation(self, get_signed_upload_url_mock, test_urls):
        """Test document creation."""
        get_signed_upload_url_mock.return_value = 'http://document-about-ocelots'

        url = reverse('test-document-collection')

        response = self.api_client.post(
            url,
            data={
                'original_filename': 'test.txt',
                'my_field': 'cats cannot taste sweet',
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.data
        assert response_data['original_filename'] == 'test.txt'
        assert response_data['my_field'] == 'cats cannot taste sweet'

        entity_document = MyEntityDocument.objects.get(pk=response_data['id'])
        assert response_data == {
            'id': str(entity_document.pk),
            'my_field': entity_document.my_field,
            'original_filename': entity_document.original_filename,
            'url': entity_document.url,
            'signed_upload_url': 'http://document-about-ocelots',
            'status': 'not_virus_scanned',
        }

    def test_document_retrieval(self, test_urls):
        """Tests retrieval of individual document."""
        entity_document = MyEntityDocument.objects.create(
            original_filename='test.txt',
            my_field='cats are lactose intolerant',
        )

        url = reverse(
            'test-document-item',
            kwargs={
                'entity_document_pk': entity_document.pk,
            },
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'id': str(entity_document.pk),
            'my_field': 'cats are lactose intolerant',
            'original_filename': entity_document.original_filename,
            'url': entity_document.url,
            'status': 'not_virus_scanned',
        }

    def test_document_with_deletion_pending_retrieval(self, test_urls):
        """Tests retrieval of individual document that is pending deletion."""
        entity_document = MyEntityDocument.objects.create(
            original_filename='test.txt',
            my_field='large field',
        )
        entity_document.document.mark_deletion_pending()

        url = reverse(
            'test-document-item',
            kwargs={
                'entity_document_pk': entity_document.pk,
            },
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('datahub.documents.tasks.virus_scan_document.apply_async')
    def test_document_schedule_virus_scan(
        self,
        virus_scan_document,
        test_urls,
    ):
        """Tests that a virus scan of the document is scheduled."""
        entity_document = MyEntityDocument.objects.create(
            original_filename='test.txt',
            my_field='cats use whiskers to navigate in the dark',
        )

        url = reverse(
            'test-document-item-callback',
            kwargs={
                'entity_document_pk': entity_document.pk,
            },
        )

        response = self.api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['status'] == 'virus_scanning_scheduled'
        virus_scan_document.assert_called_once_with(
            args=(str(entity_document.document.pk),),
        )

    @patch('datahub.documents.tasks.delete_document.apply_async')
    def test_document_delete(self, delete_document, test_urls):
        """Tests document deletion."""
        entity_document = MyEntityDocument.objects.create(
            original_filename='test.txt',
            my_field='cats can recognise human voices',
        )
        entity_document.document.uploaded_on = now()

        document_pk = entity_document.document.pk

        url = reverse('test-document-item', kwargs={'entity_document_pk': entity_document.pk})

        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        delete_document.assert_called_once_with(args=(document_pk,))

        entity_document.document.refresh_from_db()
        assert entity_document.document.status == UploadStatus.DELETION_PENDING

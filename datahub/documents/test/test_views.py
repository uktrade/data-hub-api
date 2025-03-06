"""Tests for generic document views."""
import logging
import uuid

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from unittest.mock import Mock, patch

import pytest

from django.test.utils import override_settings
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)
from datahub.documents.models import (
    Document,
    GenericDocument,
)
from datahub.documents.test.factories import CompanySharePointDocumentFactory
from datahub.documents.test.my_entity_document.models import MyEntityDocument
from datahub.documents.test.test_utils import assert_retrieved_generic_document


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
DOCUMENT_COLLECTION_URL = reverse('api-v4:document:generic-document-collection')


def document_item_url(pk: uuid.uuid4) -> str:
    return reverse('api-v4:document:generic-document-item', kwargs={'pk': pk})


@pytest.fixture
def test_urls():  # noqa: D403
    """Pytest fixture to override the ROOT_URLCONF with test views."""
    with override_settings(ROOT_URLCONF='datahub.documents.test.my_entity_document.urls'):
        yield


@pytest.fixture
def test_user_with_view_permissions():
    return create_test_user(permission_codenames=['view_genericdocument'])


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

    def test_document_schedule_virus_scan(
        self,
        monkeypatch,
        test_urls,
    ):
        """Tests that a virus scan of the document is called."""
        mock_schedule_virus_scan_document = Mock()
        monkeypatch.setattr(
            'datahub.documents.models.schedule_virus_scan_document',
            mock_schedule_virus_scan_document,
        )

        response, entity_document = self.mock_document_item()

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['status'] == 'virus_scanning_scheduled'
        mock_schedule_virus_scan_document.assert_called_once_with(
            str(entity_document.document.pk),
        )

    def mock_document_item(self):
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
        return response, entity_document

    def test_schedule_virus_scan_document(
        self,
        caplog,
        monkeypatch,
        test_urls,
    ):
        """Tests that a virus scan of the document is scheduled."""
        caplog.set_level(logging.INFO)
        response, entity_document = self.mock_document_item()

        assert response.status_code == status.HTTP_200_OK
        assert any('schedule_virus_scan_document' in message for message in caplog.messages)

    def mock_document_upload(self, s3_stubber):
        entity_document = MyEntityDocument.objects.create(
            original_filename='test.txt',
            my_field='cats can recognise human voices',
        )
        entity_document.document.uploaded_on = now()
        url = reverse('test-document-item', kwargs={'entity_document_pk': entity_document.pk})

        s3_stubber.add_response(
            'delete_object',
            {
                'ResponseMetadata': {
                    'HTTPStatusCode': 204,
                },
            },
        )
        response = self.api_client.delete(url)

        return response, entity_document

    def test_document_delete(self, caplog, s3_stubber, monkeypatch, test_urls):
        """Tests document deletion."""
        caplog.set_level(logging.INFO, 'datahub.documents.tasks')

        response, entity_document = self.mock_document_upload(s3_stubber)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert any('schedule_delete_document' in message for message in caplog.messages)

        with pytest.raises(Document.DoesNotExist):
            entity_document.document.refresh_from_db()

    def test_schedule_document_delete(self, monkeypatch, s3_stubber, test_urls):
        """Tests schedule of document deletion."""
        mock_schedule_delete_document = Mock()
        monkeypatch.setattr(
            'datahub.documents.views.schedule_delete_document',
            mock_schedule_delete_document,
        )

        response, entity_document = self.mock_document_upload(s3_stubber)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        mock_schedule_delete_document.assert_called_once_with(entity_document.document.pk)


class TestRetrieveGenericDocumentView(APITestMixin):
    """Tests for retrieving a single generic document."""

    def test_retrieve_document(self, test_user_with_view_permissions):
        document = CompanySharePointDocumentFactory()
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        url = document_item_url(document.pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert_retrieved_generic_document(document, response.data)

    def test_retrieve_non_existent_document(self, test_user_with_view_permissions):
        non_existent_pk = uuid.uuid4()
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        url = document_item_url(non_existent_pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestListGenericDocumentView(APITestMixin):
    """Tests for retrieving a list of generic documents."""

    def test_list_documents(self, test_user_with_view_permissions):
        document = CompanySharePointDocumentFactory()
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(DOCUMENT_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert_retrieved_generic_document(document, response.data['results'][0])

    def test_list_no_documents(self, test_user_with_view_permissions):
        """Tests that an empty list is returned if there are no documents."""
        assert GenericDocument.objects.count() == 0
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(DOCUMENT_COLLECTION_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []

    def test_pagination(self, test_user_with_view_permissions):
        """Test that LimitOffsetPagination is enabled for this view"""
        number_of_documents = 3
        pagination_limit = 2
        CompanySharePointDocumentFactory.create_batch(number_of_documents)
        assert GenericDocument.objects.count() == number_of_documents
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(DOCUMENT_COLLECTION_URL, data={'limit': pagination_limit})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == number_of_documents
        assert response.data['next'] is not None
        assert len(response.data['results']) == pagination_limit

    def test_sorting_by_created_on(self, test_user_with_view_permissions):
        now = datetime.now(tz=timezone.utc)
        with freeze_time(now) as frozen_datetime:
            CompanySharePointDocumentFactory(created_on=now)

        yesterday = now - timedelta(days=1)
        with freeze_time(yesterday) as frozen_datetime:
            CompanySharePointDocumentFactory(created_on=frozen_datetime)

        api_client = self.create_api_client(user=test_user_with_view_permissions)

        # Descending
        response = api_client.get(DOCUMENT_COLLECTION_URL, data={'sortby': '-created_on'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['created_on'] == now.strftime(DATETIME_FORMAT)
        assert response.data['results'][1]['created_on'] == yesterday.strftime(DATETIME_FORMAT)

        # Ascending
        response = api_client.get(DOCUMENT_COLLECTION_URL, data={'sortby': 'created_on'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['created_on'] == yesterday.strftime(DATETIME_FORMAT)
        assert response.data['results'][1]['created_on'] == now.strftime(DATETIME_FORMAT)

    def test_filter_by_related_object_id(self, test_user_with_view_permissions):
        company = CompanyFactory()
        CompanySharePointDocumentFactory(related_object=company)
        CompanySharePointDocumentFactory()
        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(
            DOCUMENT_COLLECTION_URL,
            data={'related_object_id': str(company.id)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['related_object_id'] == str(company.id)

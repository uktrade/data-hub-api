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
    SharePointDocument,
    UploadableDocument,
    UploadStatus,
)
from datahub.documents.test.factories import (
    CompanySharePointDocumentFactory,
    CompanyUploadableDocumentFactory,
)
from datahub.documents.test.my_entity_document.models import MyEntityDocument
from datahub.documents.test.test_utils import (
    assert_retrieved_generic_document,
    assert_retrieved_uploadable_document,
)

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
DOCUMENT_COLLECTION_URL = reverse('api-v4:document:generic-document-collection')


def document_item_url(pk: uuid.uuid4) -> str:
    return reverse('api-v4:document:generic-document-item', kwargs={'pk': pk})


def document_item_upload_callback_url(pk: uuid.uuid4) -> str:
    return reverse(
        'api-v4:document:generic-document-item-upload-complete-callback',
        kwargs={'pk': pk},
    )


def document_item_download_url(pk: uuid.uuid4) -> str:
    return reverse('api-v4:document:generic-document-item-download', kwargs={'pk': pk})


@pytest.fixture
def test_urls():
    """Pytest fixture to override the ROOT_URLCONF with test views."""
    with override_settings(ROOT_URLCONF='datahub.documents.test.my_entity_document.urls'):
        yield


@pytest.fixture
def test_user_with_view_permissions():
    return create_test_user(permission_codenames=['view_genericdocument'])


@pytest.fixture
def test_user_with_add_permissions():
    return create_test_user(permission_codenames=['add_genericdocument'])


@pytest.fixture
def test_user_with_change_permissions():
    return create_test_user(permission_codenames=['change_genericdocument'])


@pytest.fixture
def test_user_with_delete_permissions():
    return create_test_user(permission_codenames=['delete_genericdocument'])


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
        """Test that LimitOffsetPagination is enabled for this view."""
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


class TestCreateGenericDocumentView(APITestMixin):
    """Tests for creating generic documents."""

    def test_created_and_modified_by_fields_are_set(self, test_user_with_add_permissions):
        api_client = self.create_api_client(user=test_user_with_add_permissions)
        payload = {
            'document_type': 'documents.sharepointdocument',
            'document_data': {
                'title': 'Project Proposal',
                'url': 'https://sharepoint.example.com/project-proposal.docx',
            },
            'related_object_type': 'company.company',
            'related_object_id': str(CompanyFactory().id),
        }
        response = api_client.post(DOCUMENT_COLLECTION_URL, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        generic_document = GenericDocument.objects.get(pk=response.data['id'])
        assert generic_document.created_by_id == test_user_with_add_permissions.id
        assert generic_document.modified_by_id == test_user_with_add_permissions.id
        assert generic_document.document.created_by.id == test_user_with_add_permissions.id
        assert generic_document.document.modified_by.id == test_user_with_add_permissions.id

    def test_missing_fields_in_payload_raise_error(self, test_user_with_add_permissions):
        api_client = self.create_api_client(user=test_user_with_add_permissions)
        response = api_client.post(DOCUMENT_COLLECTION_URL, data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        fields = ['document_type', 'document_data', 'related_object_type', 'related_object_id']
        assert set(fields).issubset(set(response.data.keys()))

    def test_invalid_document_type_raises_error(self, test_user_with_add_permissions):
        api_client = self.create_api_client(user=test_user_with_add_permissions)
        invalid_document_type = 'invalid.document_type'
        payload = {
            'document_type': invalid_document_type,
            'document_data': {
                'title': 'Project Proposal',
                'url': 'https://sharepoint.example.com/project-proposal.docx',
            },
            'related_object_type': 'company.company',
            'related_object_id': str(CompanyFactory().id),
        }
        response = api_client.post(DOCUMENT_COLLECTION_URL, data=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['document_type'][0] == (
            f'Unsupported document type: {invalid_document_type}.'
            " Format should be 'app_label.model'."
        )

    def test_non_existent_related_object_type_raises_error(self, test_user_with_add_permissions):
        api_client = self.create_api_client(user=test_user_with_add_permissions)
        non_existent_related_object_type = 'non_existent.related_object_type'
        payload = {
            'document_type': 'documents.sharepointdocument',
            'document_data': {
                'title': 'Project Proposal',
                'url': 'https://sharepoint.example.com/project-proposal.docx',
            },
            'related_object_type': non_existent_related_object_type,
            'related_object_id': str(CompanyFactory().id),
        }
        response = api_client.post(DOCUMENT_COLLECTION_URL, data=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['related_object_type'][0] == (
            f'Invalid related object type: {non_existent_related_object_type}.'
            " Format should be 'app_label.model'."
        )

    def test_non_existent_related_object_raises_error(self, test_user_with_add_permissions):
        api_client = self.create_api_client(user=test_user_with_add_permissions)
        non_existent_related_object_id = uuid.uuid4()
        payload = {
            'document_type': 'documents.sharepointdocument',
            'document_data': {
                'title': 'Project Proposal',
                'url': 'https://sharepoint.example.com/project-proposal.docx',
            },
            'related_object_type': 'company.company',
            'related_object_id': str(non_existent_related_object_id),
        }
        response = api_client.post(DOCUMENT_COLLECTION_URL, data=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data['non_field_errors'][0]
            == f'Related object with id {non_existent_related_object_id} does not exist.'
        )

    def test_upload_complete_callback_with_uploadable_document_schedules_av_scan(
        self,
        test_user_with_add_permissions,
    ):
        generic_document = CompanyUploadableDocumentFactory()
        uploadable_document = generic_document.document
        api_client = self.create_api_client(user=test_user_with_add_permissions)

        with patch('datahub.documents.models.Document.schedule_av_scan') as mock_schedule_scan:
            response = api_client.post(document_item_upload_callback_url(generic_document.id))

        assert response.status_code == status.HTTP_200_OK
        mock_schedule_scan.assert_called_once()

        assert_retrieved_generic_document(generic_document, response.data)
        assert_retrieved_uploadable_document(uploadable_document, response.data['document'])

    def test_upload_complete_callback_with_non_uploadable_document_returns_error(
        self,
        test_user_with_add_permissions,
    ):
        generic_document = CompanySharePointDocumentFactory()
        api_client = self.create_api_client(user=test_user_with_add_permissions)

        response = api_client.post(document_item_upload_callback_url(generic_document.id))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'This action is only available for uploadable documents'

    def test_download_uploadable_document_returns_document(self, test_user_with_view_permissions):
        generic_document = CompanyUploadableDocumentFactory()
        uploadable_document = generic_document.document
        download_url = 'https://example.com/test-download-url'

        uploadable_document.document.mark_as_scanned(av_clean=True, av_reason='')

        api_client = self.create_api_client(user=test_user_with_view_permissions)

        with patch('datahub.documents.models.Document.get_signed_url') as mock_get_signed_url:
            mock_get_signed_url.return_value = download_url
            response = api_client.get(document_item_download_url(generic_document.id))

        assert response.status_code == status.HTTP_200_OK
        assert_retrieved_generic_document(generic_document, response.data)
        assert_retrieved_uploadable_document(uploadable_document, response.data['document'])
        assert 'document_url' in response.data
        assert response.data['document_url'] == download_url

    def test_download_unscanned_document_returns_error(self, test_user_with_view_permissions):
        generic_document = CompanyUploadableDocumentFactory()

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(document_item_download_url(generic_document.id))

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_download_virus_infected_document_returns_error(self, test_user_with_view_permissions):
        generic_document = CompanyUploadableDocumentFactory()
        uploadable_document = generic_document.document

        uploadable_document.document.mark_as_scanned(av_clean=False, av_reason='Virus detected')

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(document_item_download_url(generic_document.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Document did not pass virus scanning' in response.data['detail']

    def test_download_non_uploadable_document_returns_error(self, test_user_with_view_permissions):
        generic_document = CompanySharePointDocumentFactory()

        api_client = self.create_api_client(user=test_user_with_view_permissions)
        response = api_client.get(document_item_download_url(generic_document.id))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'This action is only available for uploadable documents'


class TestCreateCompanySharePointDocumentView(APITestMixin):
    """Tests for creating company sharepoint documents, specifically."""

    def test_generic_document_is_created(self, test_user_with_add_permissions):
        assert GenericDocument.objects.count() == 0

        api_client = self.create_api_client(user=test_user_with_add_permissions)
        payload = {
            'document_type': 'documents.sharepointdocument',
            'document_data': {
                'title': 'Project Proposal',
                'url': 'https://sharepoint.example.com/project-proposal.docx',
            },
            'related_object_type': 'company.company',
            'related_object_id': str(CompanyFactory().id),
        }
        response = api_client.post(DOCUMENT_COLLECTION_URL, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert GenericDocument.objects.count() == 1
        assert GenericDocument.objects.filter(pk=response.data['id']).exists()

    def test_sharepoint_document_is_also_created(self, test_user_with_add_permissions):
        assert SharePointDocument.objects.count() == 0

        api_client = self.create_api_client(user=test_user_with_add_permissions)
        payload = {
            'document_type': 'documents.sharepointdocument',
            'document_data': {
                'title': 'Project Proposal',
                'url': 'https://sharepoint.example.com/project-proposal.docx',
            },
            'related_object_type': 'company.company',
            'related_object_id': str(CompanyFactory().id),
        }
        response = api_client.post(DOCUMENT_COLLECTION_URL, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert SharePointDocument.objects.count() == 1
        generic_document = GenericDocument.objects.get(pk=response.data['id'])
        assert SharePointDocument.objects.filter(pk=generic_document.document_object_id).exists()

        for attribute, value in payload['document_data'].items():
            assert getattr(generic_document.document, attribute) == value

    def test_company_is_linked(self, test_user_with_add_permissions):
        company = CompanyFactory()

        api_client = self.create_api_client(user=test_user_with_add_permissions)
        payload = {
            'document_type': 'documents.sharepointdocument',
            'document_data': {
                'title': 'Project Proposal',
                'url': 'https://sharepoint.example.com/project-proposal.docx',
            },
            'related_object_type': 'company.company',
            'related_object_id': str(company.id),
        }
        response = api_client.post(DOCUMENT_COLLECTION_URL, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        generic_document = GenericDocument.objects.get(pk=response.data['id'])
        assert generic_document.related_object == company


class TestCreateCompanyUploadableDocumentView(APITestMixin):
    """Tests for creating company uploadable documents."""

    def test_uploadable_document_is_created(self, test_user_with_add_permissions):
        """Also tests a generic document is created and linked to the company."""
        company = CompanyFactory()
        upload_url = 'https://example.com/test-upload-url'

        api_client = self.create_api_client(user=test_user_with_add_permissions)
        payload = {
            'document_type': 'documents.uploadabledocument',
            'document_data': {
                'original_filename': 'test.pdf',
                'title': 'Test Document',
            },
            'related_object_type': 'company.company',
            'related_object_id': str(company.id),
        }

        with patch(
            'datahub.documents.models.Document.get_signed_upload_url',
        ) as mock_get_signed_upload_url:
            mock_get_signed_upload_url.return_value = upload_url
            response = api_client.post(DOCUMENT_COLLECTION_URL, data=payload)

        assert response.status_code == status.HTTP_201_CREATED

        assert GenericDocument.objects.count() == 1
        assert UploadableDocument.objects.count() == 1
        assert Document.objects.count() == 1

        generic_document = GenericDocument.objects.first()
        uploadable_document = generic_document.document

        assert_retrieved_generic_document(generic_document, response.data)
        assert_retrieved_uploadable_document(uploadable_document, response.data['document'])

        assert uploadable_document.document.status == UploadStatus.NOT_VIRUS_SCANNED
        assert 'signed_upload_url' in response.data
        assert response.data['signed_upload_url'] == upload_url

        assert generic_document.related_object == company

    @patch('datahub.documents.utils.get_s3_client_for_bucket')
    def test_uploadable_document_uses_default_credentials(
        self,
        mock_get_s3_client,
        test_user_with_add_permissions,
    ):
        upload_url = 'https://example.com/test-upload-url'

        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_s3_client.generate_presigned_url.return_value = upload_url

        api_client = self.create_api_client(user=test_user_with_add_permissions)
        payload = {
            'document_type': 'documents.uploadabledocument',
            'document_data': {
                'original_filename': 'test.pdf',
                'title': 'Test Document',
            },
            'related_object_type': 'company.company',
            'related_object_id': str(CompanyFactory().id),
        }

        response = api_client.post(DOCUMENT_COLLECTION_URL, data=payload)
        assert response.status_code == status.HTTP_201_CREATED

        generic_document = GenericDocument.objects.get(pk=response.data['id'])
        uploadable_document = generic_document.document
        assert uploadable_document.document.use_default_credentials is True

        mock_get_s3_client.assert_called_with(
            uploadable_document.document.bucket_id,
            use_default_credentials=True,
        )

        mock_s3_client.generate_presigned_url.assert_called_with(
            ClientMethod='put_object',
            Params={
                'Bucket': uploadable_document.document.bucket_id,
                'Key': uploadable_document.document.path,
            },
            ExpiresIn=3600,
        )


class TestDeleteGenericDocumentView(APITestMixin):
    """Tests for deleting generic documents."""

    def test_generic_document_is_archived(self, test_user_with_delete_permissions):
        generic_document = CompanySharePointDocumentFactory()
        assert generic_document.archived is False
        assert GenericDocument.objects.count() == 1

        api_client = self.create_api_client(user=test_user_with_delete_permissions)
        response = api_client.delete(document_item_url(generic_document.pk))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        generic_document.refresh_from_db()
        assert generic_document.archived is True
        assert GenericDocument.objects.count() == 1

    def test_specific_type_document_is_also_archived(self, test_user_with_delete_permissions):
        generic_document = CompanySharePointDocumentFactory()
        sharepoint_document = generic_document.document

        assert sharepoint_document.archived is False
        assert SharePointDocument.objects.count() == 1

        api_client = self.create_api_client(user=test_user_with_delete_permissions)
        response = api_client.delete(document_item_url(generic_document.pk))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        sharepoint_document.refresh_from_db()
        assert sharepoint_document.archived is True
        assert SharePointDocument.objects.count() == 1

    @patch('datahub.documents.views.schedule_delete_document')
    def test_uploadable_document_is_deleted(
        self,
        mock_schedule_delete,
        test_user_with_delete_permissions,
    ):
        generic_document = CompanyUploadableDocumentFactory()
        uploadable_document = generic_document.document
        assert uploadable_document.document.status == UploadStatus.NOT_VIRUS_SCANNED

        api_client = self.create_api_client(user=test_user_with_delete_permissions)
        response = api_client.delete(document_item_url(generic_document.pk))

        assert response.status_code == status.HTTP_204_NO_CONTENT

        uploadable_document.refresh_from_db()
        assert uploadable_document.document.status == UploadStatus.DELETION_PENDING
        mock_schedule_delete.assert_called_once_with(uploadable_document.document.id)

        # Uploadable document instances, linked to documents that are pending deletion,
        # are excluded from the queryset as per EntityDocumentManager.get_queryset
        assert not UploadableDocument.objects.filter(pk=uploadable_document.id).exists()

        # Conversely, the generic document instances will be archived
        assert GenericDocument.objects.filter(pk=generic_document.id).exists()
        generic_document.refresh_from_db()
        assert generic_document.archived is True

    @patch('datahub.documents.utils.get_s3_client_for_bucket')
    def test_uploadable_document_uses_default_credentials(
        self,
        mock_get_s3_client,
        test_user_with_delete_permissions,
    ):
        generic_document = CompanyUploadableDocumentFactory()
        uploadable_document = generic_document.document
        assert uploadable_document.document.use_default_credentials is True

        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client

        api_client = self.create_api_client(user=test_user_with_delete_permissions)
        response = api_client.delete(document_item_url(generic_document.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT

        mock_get_s3_client.assert_called_with(
            uploadable_document.document.bucket_id,
            use_default_credentials=True,
        )

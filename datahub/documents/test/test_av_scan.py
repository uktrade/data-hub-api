from io import BytesIO
from unittest.mock import patch

import pytest
from requests.exceptions import HTTPError
from requests_toolbelt.multipart.decoder import MultipartDecoder
from rest_framework import status

from datahub.documents.av_scan import _multipart_encoder, StreamWrapper, VirusScanException
from datahub.documents.models import Document, UploadStatus
from datahub.documents.tasks import virus_scan_document
from datahub.documents.test.factories import DocumentFactory

pytestmark = pytest.mark.django_db


@patch.object(Document, 'get_signed_url')
def test_virus_scan_document_clean(get_signed_url_mock, requests_mock):
    """Tests virus scanning a clean file."""
    get_signed_url_mock.return_value = 'http://url'
    document = DocumentFactory()
    requests_mock.get(
        'http://url',
        text='hello!',
        headers={
            'Content-Type': 'application/json',
            'Content-Length': '1000',
        },
    )
    requests_mock.post(
        'http://av-service/',
        json={
            'malware': False,
            'reason': None,
            'time': 0.2,
        },
    )

    virus_scan_document.apply(args=(str(document.id), )).get()
    document.refresh_from_db()
    assert document.av_clean is True


@patch.object(Document, 'get_signed_url')
def test_virus_scan_document_infected(get_signed_url_mock, requests_mock):
    """Tests virus scanning a clean file."""
    get_signed_url_mock.return_value = 'http://url'
    document = DocumentFactory()
    requests_mock.get(
        'http://url',
        text='hello!',
        headers={
            'Content-Type': 'application/json',
            'Content-Length': '1000',
        },
    )
    requests_mock.post(
        'http://av-service/',
        json={
            'malware': True,
            'reason': 'File contains ransomware.',
            'time': 0.1,
        },
    )

    virus_scan_document.apply(args=(str(document.id), )).get()
    document.refresh_from_db()
    assert document.av_clean is False


@patch.object(Document, 'get_signed_url')
def test_virus_scan_document_bad_response_body(get_signed_url_mock, requests_mock):
    """Tests handling of unexpected response bodies from the AV service."""
    get_signed_url_mock.return_value = 'http://url'
    document = DocumentFactory()
    requests_mock.get(
        'http://url',
        text='hello!',
        headers={
            'Content-Type': 'application/json',
            'Content-Length': '1000',
        },
    )
    requests_mock.post(
        'http://av-service/',
        json={
            'too_many_cats': 'never',
        },
    )

    error_message = (
        f"Unexpected response from AV service: {{'too_many_cats': 'never'}} "
        f'when scanning document with ID {document.pk}'
    )

    with pytest.raises(
        VirusScanException,
        match=error_message,
    ):
        virus_scan_document.apply(args=(str(document.id), )).get()

    document.refresh_from_db()
    assert document.av_clean is None
    assert document.status == UploadStatus.VIRUS_SCANNING_FAILED
    assert document.av_reason == error_message


@patch.object(Document, 'get_signed_url')
def test_virus_scan_document_file_not_found(get_signed_url_mock, requests_mock):
    """Tests handling of a not found error from URL."""
    get_signed_url_mock.return_value = 'http://url'
    document = DocumentFactory()
    requests_mock.get(
        'http://url',
        status_code=404,
    )
    with pytest.raises(
        VirusScanException,
        match=rf'Unable to download the document with ID {document.pk} '
              rf'for scanning \(status_code\=404\).',
    ):
        virus_scan_document.apply(args=(str(document.id), )).get()
    document.refresh_from_db()
    assert document.av_clean is None


@patch.object(Document, 'get_signed_url')
def test_virus_scan_document_bad_response_status(get_signed_url_mock, requests_mock):
    """Tests handling of error response statuses from the AV service."""
    get_signed_url_mock.return_value = 'http://url'
    document = DocumentFactory()
    requests_mock.get(
        'http://url',
        text='hello!',
        headers={
            'Content-Type': 'application/json',
            'Content-Length': '1000',
        },
    )
    requests_mock.post(
        'http://av-service/',
        status_code=status.HTTP_400_BAD_REQUEST,
    )

    with pytest.raises(HTTPError) as excinfo:
        virus_scan_document.apply(args=(str(document.id), )).get()
    document.refresh_from_db()
    assert document.av_clean is None
    assert str(excinfo.value) == '400 Client Error: None for url: http://av-service/'


def test_file_is_being_encoded():
    """Test if file is being encoded."""
    data = bytes([0x13] * 1024)

    stream = StreamWrapper(BytesIO(data), 1024)

    form = _multipart_encoder('test', stream, 'application/x-binary')
    response_data = form.read()
    decoder = MultipartDecoder(response_data, form.content_type)

    assert decoder.parts[0].content == data

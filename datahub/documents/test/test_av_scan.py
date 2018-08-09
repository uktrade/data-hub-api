from io import BytesIO
from unittest.mock import patch

import pytest
from requests.exceptions import HTTPError
from rest_framework import status

from .factories import DocumentFactory
from ..av_scan import VirusScanException
from ..models import Document, UPLOAD_STATUSES
from ..tasks import virus_scan_document

pytestmark = pytest.mark.django_db


MOCK_S3_RESPONSE = {
    'Body': BytesIO(b'123456'),
    'ContentLength': 6,
    'ContentType': 'text/plain'
}


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
        }
    )
    requests_mock.post('http://av-service/', text='OK')

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
        }
    )
    requests_mock.post('http://av-service/', text='NOTOK')

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
        }
    )
    requests_mock.post('http://av-service/', text='BADRESPONSE')

    error_message = (
        f'Unexpected response from AV service: BADRESPONSE '
        f'when scanning document with ID {document.pk}'
    )

    with pytest.raises(
        VirusScanException,
        match=error_message
    ):
        virus_scan_document.apply(args=(str(document.id), )).get()

    document.refresh_from_db()
    assert document.av_clean is None
    assert document.status == UPLOAD_STATUSES.virus_scanning_failed
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
        match=f'Unable to download the document with ID {document.pk} '
              f'for scanning \(status_code\=404\).'
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
        }
    )
    requests_mock.post(
        'http://av-service/',
        text='OK',
        status_code=status.HTTP_400_BAD_REQUEST,
    )

    with pytest.raises(HTTPError) as excinfo:
        virus_scan_document.apply(args=(str(document.id), )).get()
    document.refresh_from_db()
    assert document.av_clean is None
    assert str(excinfo.value) == '400 Client Error: None for url: http://av-service/'

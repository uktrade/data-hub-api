from io import BytesIO

import pytest
from botocore.exceptions import ClientError
from requests.exceptions import HTTPError
from rest_framework import status

from datahub.documents import av_scan
from datahub.documents.av_scan import VirusScanException
from datahub.documents.test.factories import DocumentFactory

pytestmark = pytest.mark.django_db


MOCK_S3_RESPONSE = {
    'Body': BytesIO(b'123456'),
    'ContentLength': 6,
    'ContentType': 'text/plain'
}


def test_virus_scan_document_clean(s3_stubber, requests_mock):
    """Tests virus scanning a clean file."""
    document = DocumentFactory()
    s3_stubber.add_response('get_object', MOCK_S3_RESPONSE, expected_params={
        'Bucket': document.s3_bucket, 'Key': document.s3_key
    })
    requests_mock.post('http://av-service/', text='OK')

    av_scan.virus_scan_document(str(document.id))
    document.refresh_from_db()
    assert document.av_clean is True


def test_virus_scan_document_infected(s3_stubber, requests_mock):
    """Tests virus scanning a clean file."""
    document = DocumentFactory()
    s3_stubber.add_response('get_object', MOCK_S3_RESPONSE, expected_params={
        'Bucket': document.s3_bucket, 'Key': document.s3_key
    })
    requests_mock.post('http://av-service/', text='NOTOK')

    av_scan.virus_scan_document(str(document.id))
    document.refresh_from_db()
    assert document.av_clean is False


def test_virus_scan_document_bad_response_body(s3_stubber, requests_mock, caplog):
    """Tests handling of unexpected response bodies from the AV service."""
    document = DocumentFactory()
    s3_stubber.add_response('get_object', MOCK_S3_RESPONSE, expected_params={
        'Bucket': document.s3_bucket, 'Key': document.s3_key
    })
    requests_mock.post('http://av-service/', text='BADRESPONSE')

    with pytest.raises(VirusScanException):
        av_scan.virus_scan_document(str(document.id))

    document.refresh_from_db()
    assert document.av_clean is None


def test_virus_scan_document_s3_key_not_found(s3_stubber, requests_mock, caplog):
    """Tests handling of a not found error from S3."""
    document = DocumentFactory()
    s3_stubber.add_client_error(
        'get_object', service_error_code='NoSuchKey', http_status_code=404,
        expected_params={'Bucket': document.s3_bucket, 'Key': document.s3_key}
    )

    with pytest.raises(ClientError) as exc:
        av_scan.virus_scan_document(str(document.id))
    document.refresh_from_db()
    assert document.av_clean is None
    assert exc.value.response['Error']['Code'] == 'NoSuchKey'


def test_virus_scan_document_bad_response_status(s3_stubber, requests_mock, caplog):
    """Tests handling of error response statuses from the AV service."""
    document = DocumentFactory()
    s3_stubber.add_response('get_object', MOCK_S3_RESPONSE, expected_params={
        'Bucket': document.s3_bucket, 'Key': document.s3_key
    })
    requests_mock.post(
        'http://av-service/',
        text='OK',
        status_code=status.HTTP_400_BAD_REQUEST,
    )

    with pytest.raises(HTTPError) as exc:
        av_scan.virus_scan_document(str(document.id))
    document.refresh_from_db()
    assert document.av_clean is None
    assert exc.value.response.status_code == status.HTTP_400_BAD_REQUEST

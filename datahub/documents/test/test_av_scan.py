from io import BytesIO

import pytest
import requests_mock
from botocore.stub import Stubber

from datahub.core.utils import get_s3_client
from datahub.documents import av_scan
from datahub.documents.test.factories import DocumentFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def requests_stubber():
    """Requests stubber based on requests-mock"""
    with requests_mock.mock() as requests_stubber:
        yield requests_stubber


@pytest.fixture()
def s3_stubber():
    """S3 stubber using the botocore Stubber class"""
    s3_client = get_s3_client()
    with Stubber(s3_client) as s3_stubber:
        yield s3_stubber


def test_virus_scan_document_clean(s3_stubber, requests_stubber):
    """Tests virus scanning a clean file."""
    s3_response = {
        'Body': BytesIO(b'123456'),
        'ContentLength': 6,
        'ContentType': 'text/plain'
    }
    document = DocumentFactory()
    s3_stubber.add_response('get_object', s3_response, expected_params={
        'Bucket': document.s3_bucket, 'Key': document.s3_key
    })
    requests_stubber.post('http://av-service/', text='OK')

    av_scan.virus_scan_document(str(document.id))
    document.refresh_from_db()
    assert document.av_clean is True


def test_virus_scan_document_infected(s3_stubber, requests_stubber):
    """Tests virus scanning a clean file."""
    s3_response = {
        'Body': BytesIO(b'123456'),
        'ContentLength': 6,
        'ContentType': 'text/plain'
    }
    document = DocumentFactory()
    s3_stubber.add_response('get_object', s3_response, expected_params={
        'Bucket': document.s3_bucket, 'Key': document.s3_key
    })
    requests_stubber.post('http://av-service/', text='NOTOK')

    av_scan.virus_scan_document(str(document.id))
    document.refresh_from_db()
    assert document.av_clean is False

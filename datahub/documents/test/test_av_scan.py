from io import BytesIO

import pytest
import requests_mock
from botocore.stub import Stubber
from django.test.utils import override_settings

from datahub.core.utils import get_s3_client
from datahub.documents import av_scan
from datahub.documents.test.factories import DocumentFactory

pytestmark = pytest.mark.django_db


def test_virus_scan_document_clean():
    """Tests virus scanning a clean file."""
    s3_client = get_s3_client()
    stubber = Stubber(s3_client)
    s3_response = {
        'Body': BytesIO(b'123456'),
        'ContentLength': 6,
        'ContentType': 'text/plain'
    }
    document = DocumentFactory()
    stubber.add_response('get_object', s3_response, expected_params={
        'Bucket': document.s3_bucket, 'Key': document.s3_key
    })

    with override_settings(DOCUMENT_BUCKET='test-bucket', AV_SERVICE_URL='http://av-service/'), \
            stubber, requests_mock.mock() as requests_stubber:
        requests_stubber.post('http://av-service/', text='OK')
        av_scan.virus_scan_document(str(document.id))
        document.refresh_from_db()
        assert document.av_clean is True

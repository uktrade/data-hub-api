from contextlib import closing
from logging import getLogger

import requests
from django.conf import settings
from django.utils.timezone import now
from raven.contrib.django.raven_compat.models import client
from requests_toolbelt.multipart.encoder import MultipartEncoder

from datahub.core.exceptions import DataHubException
from datahub.core.utils import get_s3_client
from datahub.documents.models import Document

logger = getLogger(__name__)


class S3StreamingBodyWrapper:
    """S3 Object wrapper that plays nice with streamed multipart/form-data."""

    def __init__(self, s3_obj):
        """Init wrapper, and grab interesting bits from s3 object."""
        self._obj = s3_obj
        self._body = s3_obj['Body']
        self._remaining_bytes = s3_obj['ContentLength']

    def read(self, amt=-1):
        """Read given amount of bytes, and decrease remaining len."""
        content = self._body.read(amt)
        self._remaining_bytes -= len(content)

        return content

    def __len__(self):
        """Return remaining bytes, that have not been read yet."""
        return self._remaining_bytes


def init_document_av_scan(doc_pk: str):
    """Stream file to the AV service."""
    try:
        _process_document(doc_pk)
    except Exception:
        logger.exception('Error virus scanning document')
        client.captureException()


def _process_document(doc_pk: str):
    if not settings.AV_SERVICE_URL:
        raise VirusScanException(f'Cannot scan document with ID {doc_pk}; AV service URL not'
                                 f'configured')

    doc = Document.objects.get(pk=doc_pk)
    doc.scan_initiated_on = now()
    doc.save()

    is_file_clean = _scan_s3_object(doc.filename, doc.s3_bucket, doc.s3_key)

    doc.scanned_on = now()
    doc.av_clean = is_file_clean
    doc.save()


def _scan_s3_object(original_filename, bucket, key):
    s3_client = get_s3_client()
    response = s3_client.get_object(Bucket=bucket, Key=key)
    with closing(response['Body']):
        return _scan_raw_file(
            original_filename, S3StreamingBodyWrapper(response), response['ContentType']
        )


def _scan_raw_file(filename, file_object, content_type):
    multipart_fields = {
        'file': (
            filename,
            file_object,
            content_type,
        )
    }
    encoder = MultipartEncoder(fields=multipart_fields)

    response = requests.post(
        # Assumes HTTP Basic auth in URL
        # see: https://github.com/uktrade/dit-clamav-rest
        settings.AV_SERVICE_URL,
        data=encoder,
        headers={'Content-Type': encoder.content_type},
    )
    response.raise_for_status()
    if response.text not in ('OK', 'NOTOK'):
        raise VirusScanException(f'Unexpected response from AV service: {response.content}')
    return response.text == 'OK'


class VirusScanException(DataHubException):
    """Exceptions raised when scanning documents for viruses."""

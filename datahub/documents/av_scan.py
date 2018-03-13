from contextlib import closing
from logging import getLogger

import requests
from django.conf import settings
from django.utils.timezone import now
from django_pglocks import advisory_lock
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
        """Return remaining bytes, that have not been read yet.

        requests-toolbelt expects this to return the number of unread bytes (rather than
        the total length of the stream).
        """
        return self._remaining_bytes


def virus_scan_document(document_pk: str):
    """Virus scans an uploaded document.

    This is intended to be run in the thread pool executor. The file is streamed from S3 to the
    anti-virus service.

    Any errors are logged and sent to Sentry.
    """
    with advisory_lock(f'av-scan-{document_pk}'):
        _process_document(document_pk)


def _process_document(document_pk: str):
    """Virus scans an uploaded document."""
    if not settings.AV_SERVICE_URL:
        raise VirusScanException(f'Cannot scan document with ID {document_pk}; AV service URL not'
                                 f'configured')

    doc = Document.objects.get(pk=document_pk)
    if doc.scan_initiated_on is not None:
        warn_msg = f'Skipping scan of doc:{document_pk}, scan already initiated'
        logger.warning(warn_msg)
        client.captureMessage(warn_msg)
        return

    doc.scan_initiated_on = now()
    doc.save()

    is_file_clean = _scan_s3_object(doc.filename, doc.s3_bucket, doc.s3_key)

    doc.scanned_on = now()
    doc.av_clean = is_file_clean
    doc.save()


def _scan_s3_object(original_filename, bucket, key):
    """Virus scans a file stored in S3."""
    s3_client = get_s3_client()
    response = s3_client.get_object(Bucket=bucket, Key=key)
    with closing(response['Body']):
        return _scan_raw_file(
            original_filename, S3StreamingBodyWrapper(response), response['ContentType']
        )


def _scan_raw_file(filename, file_object, content_type):
    """Virus scans a file-like object."""
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

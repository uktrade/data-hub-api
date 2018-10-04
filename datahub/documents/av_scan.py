from logging import getLogger

import requests
from django.conf import settings
from requests.exceptions import HTTPError
from requests_toolbelt.multipart.encoder import MultipartEncoder

from datahub.documents.exceptions import VirusScanException
from datahub.documents.utils import get_document_by_pk

logger = getLogger(__name__)


class StreamWrapper:
    """Stream wrapper that plays nice with MultipartEncoder."""

    def __init__(self, body, length):
        """Init the wrapper."""
        self._body = body
        self._remaining_bytes = int(length)

    def read(self, amount=-1):
        """Read given amount of bytes, and decrease remaining len."""
        content = self._body.read(amount)
        self._remaining_bytes -= len(content)

        return content

    def __len__(self):
        """Return remaining bytes, that have not been read yet.
        requests-toolbelt expects this to return the number of unread bytes (rather than
        the total length of the stream).
        """
        return self._remaining_bytes


def perform_virus_scan(document_pk: str, download_url: str):
    """
    Virus scans an uploaded document.

    :param document_pk: pk of a document to be scanned
    :param download_url: URL to a file to be scanned

    :raises VirusScanException: when one following of happens:
        - AV service URL is not configured
        - file couldn't be downloaded
        - unknown response returned by the AV service
    """
    if not settings.AV_V2_SERVICE_URL:
        raise VirusScanException(
            f'Cannot scan document with ID {document_pk}; AV V2 service '
            f'URL not configured',
        )

    logger.info(f'Virus scanning of Document with ID {document_pk} started.')

    document = get_document_by_pk(document_pk)
    if not document or document.scanned_on or document.scan_initiated_on:
        return

    document.mark_scan_initiated()

    try:
        result = _download_and_scan_file(str(document.pk), download_url)
    except Exception as exc:
        document.mark_scan_failed(str(exc))
        logger.error(f'Virus scanning of document with ID {document_pk} failed.')
        raise

    is_file_clean = not result['malware']
    document.mark_as_scanned(is_file_clean, result.get('reason') or '')

    logger.info(
        f'Virus scanning of Document with ID {document_pk} '
        f'completed (av_clean={is_file_clean}).',
    )


def _download_and_scan_file(document_pk: str, download_url: str):
    """Virus scans a file stored on remote server."""
    with requests.get(download_url, stream=True) as response:
        try:
            response.raise_for_status()
        except HTTPError as exc:
            raise VirusScanException(
                f'Unable to download the document with ID {document_pk} '
                f'for scanning (status_code={exc.response.status_code}).',
            ) from exc
        content = StreamWrapper(response.raw, response.headers['content-length'])
        return _scan_stream(document_pk, content, response.headers['content-type'])


def _multipart_encoder(document_pk, content, content_type):
    multipart_fields = {
        'file': (
            document_pk,
            content,
            content_type,
        ),
    }
    encoder = MultipartEncoder(multipart_fields)
    return encoder


def _scan_stream(document_pk, content, content_type):
    """Virus scans a file-like object."""
    encoder = _multipart_encoder(document_pk, content, content_type)
    response = requests.post(
        # Assumes HTTP Basic auth in URL
        # see: https://github.com/uktrade/dit-clamav-rest
        settings.AV_V2_SERVICE_URL,
        data=encoder,
        headers={'Content-Type': encoder.content_type},
    )
    response.raise_for_status()
    result = response.json()
    if 'malware' in result:
        return result

    raise VirusScanException(
        f'Unexpected response from AV service: {result} '
        f'when scanning document with ID {document_pk}',
    )

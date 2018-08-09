from logging import getLogger

import requests
from django.conf import settings
from requests.exceptions import HTTPError
from requests_toolbelt.multipart.encoder import MultipartEncoder
from requests_toolbelt.streaming_iterator import StreamingIterator

from .exceptions import VirusScanException
from .utils import get_document_by_pk

logger = getLogger(__name__)


def perform_virus_scan(document_pk: str, download_url: str):
    """
    Virus scans an uploaded document.

    :param document_pk: pk of a document to be scanned
    :param download_url: URL to a file to be scanned

    :raises VirusScanException: when one following of happens:
        - AV service is not configured
        - file couldn't be downloaded
        - unknown response returned by the AV service
    """
    if not settings.AV_SERVICE_URL:
        raise VirusScanException(f'Cannot scan document with ID {document_pk}; AV service URL not'
                                 f'configured')

    logger.info(f'Virus scanning of Document with ID {document_pk} started.')

    document = get_document_by_pk(document_pk)
    if not document or document.scanned_on or document.scan_initiated_on:
        return

    document.mark_scan_initiated()

    try:
        is_file_clean = _download_and_scan_file(str(document.pk), download_url)
    except Exception as exc:
        document.mark_scan_failed(str(exc))
        logger.error(f'Virus scanning of document with ID {document_pk} failed.')
        raise

    # TODO: add reason from v2 API response
    document.mark_as_scanned(is_file_clean, '')

    logger.info(f'Virus scanning of Document with ID {document_pk} '
                f'completed (av_clean={is_file_clean}).')


def _download_and_scan_file(document_pk: str, download_url: str):
    """Virus scans a file stored on remote server."""
    with requests.get(download_url, stream=True) as response:
        try:
            response.raise_for_status()
        except HTTPError as exc:
            raise VirusScanException(
                f'Unable to download the document with ID {document_pk} '
                f'for scanning (status_code={exc.response.status_code}).'
            ) from exc
        length = response.headers['content-length']

        content = StreamingIterator(
            length,
            response.iter_content(chunk_size=settings.AV_SERVICE_CHUNK_SIZE)
        )
        return _scan_raw_file(document_pk, content, response.headers['content-type'])


def _scan_raw_file(document_pk, content, content_type):
    """Virus scans a file-like object."""
    multipart_fields = {
        'file': (
            document_pk,
            content_type,
            content,
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
        raise VirusScanException(
            f'Unexpected response from AV service: {response.text} '
            f'when scanning document with ID {document_pk}'
        )
    return response.text == 'OK'

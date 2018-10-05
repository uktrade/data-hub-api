from logging import getLogger

from celery import shared_task
from django.db import transaction
from django_pglocks import advisory_lock

from datahub.documents.av_scan import perform_virus_scan
from datahub.documents.utils import get_document_by_pk, perform_delete_document

logger = getLogger(__name__)


@shared_task
@transaction.atomic
def delete_document(document_pk):
    """Handle document delete."""
    try:
        perform_delete_document(document_pk)
    except Exception:
        logger.error(
            f'Deletion from S3 of document with ID {document_pk} failed.',
        )
        raise


@shared_task
def virus_scan_document(document_pk: str):
    """Virus scans an uploaded document.

    The file is streamed from S3 to the anti-virus service.

    Any errors are logged and sent to Sentry.
    """
    with advisory_lock(f'av-scan-{document_pk}'):
        document = get_document_by_pk(document_pk)
        if document:
            download_url = document.get_signed_url(allow_unsafe=True)
            perform_virus_scan(document_pk, download_url)

import tempfile
from logging import getLogger

import mailparser
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from datahub.documents import utils as documents
from datahub.interaction.email_processors.processors import CalendarInteractionEmailProcessor

logger = getLogger(__name__)

BUCKET_ID = 'mailbox'


def get_mail_docs_in_bucket():
    """
    Gets all mail documents in the bucket.
    """
    if BUCKET_ID not in settings.DOCUMENT_BUCKETS:
        raise ImproperlyConfigured(f'Bucket "{BUCKET_ID}" is missing in settings')

    config = settings.DOCUMENT_BUCKETS[BUCKET_ID]
    if 'bucket' not in config:
        raise ImproperlyConfigured(f'Bucket "{BUCKET_ID}" not configured properly in settings')

    name = config['bucket']
    if not name:
        raise ImproperlyConfigured(
            f'Bucket "{BUCKET_ID}" bucket value not configured properly in settings',
        )

    client = documents.get_s3_client_for_bucket(bucket_id=BUCKET_ID)

    paginator = client.get_paginator('list_objects')
    for page in paginator.paginate(Bucket=name):
        for doc in page.get('Contents') or []:
            key = doc['Key']
            with tempfile.TemporaryFile(mode='w+b') as f:
                client.download_fileobj(Bucket=name, Key=key, Fileobj=f)
                f.seek(0)
                content = f.read()
            yield {'source': key, 'content': content}


def process_ingestion_emails():
    """
    Gets all new mail documents in the bucket and process each message.
    """
    processor = CalendarInteractionEmailProcessor()

    for message in get_mail_docs_in_bucket():
        source = message['source']
        try:
            documents.delete_document(bucket_id=BUCKET_ID, document_key=message['source'])
        except Exception as e:
            logger.exception('Error deleting message: "%s", error: "%s"', source, e)
            continue

        try:
            email = mailparser.parse_from_bytes(message['content'])
            processed, reason = processor.process_email(message=email)
            if not processed:
                logger.error('Error parsing message: "%s", error: "%s"', source, reason)
            else:
                logger.info(reason)
        except Exception as e:
            logger.exception('Error processing message: "%s", error: "%s"', source, e)

        logger.info(
            'Successfully processed message "%s" and deleted document from bucket "%s"',
            source,
            BUCKET_ID,
        )

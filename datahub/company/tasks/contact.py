import datetime
import json
import logging
import math

import environ
import requests

from dateutil import parser
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django_pglocks import advisory_lock

from smart_open import open

from datahub.company import consent
from datahub.company.models import Contact
from datahub.core.boto3_client import get_s3_client
from datahub.core.exceptions import APIBadGatewayException
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.errors import RetryError
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.core.realtime_messaging import send_realtime_message


logger = logging.getLogger(__name__)


def _automatic_contact_archive(limit=1000, simulate=False):
    contacts_to_be_archived = Contact.objects.filter(
        archived=False,
        company__archived=True,
    ).prefetch_related('company')[:limit]

    for contact in contacts_to_be_archived:
        message = f'Automatically archived contact: {contact.id}'
        if simulate:
            logger.info(f'[SIMULATION] {message}')
            continue
        contact.archived = True
        contact.archived_reason = (
            'Record was automatically archived due to the company '
            f'"{contact.company.name}" being archived'
        )
        contact.archived_on = timezone.now()
        contact.save(
            update_fields=[
                'archived',
                'archived_reason',
                'archived_on',
            ],
        )
        logger.info(message)

    return contacts_to_be_archived.count()


def schedule_update_contact_consent(
    email_address,
    accepts_dit_email_marketing,
    modified_at=None,
    **kwargs,
):
    job = job_scheduler(
        function=update_contact_consent,
        function_args=(
            email_address,
            accepts_dit_email_marketing,
            modified_at,
        ),
        function_kwargs=kwargs,
        max_retries=5,
        retry_backoff=30,
    )
    logger.info(
        f'Task {job.id} update_contact_consent',
    )
    return job


def update_contact_consent(
    email_address,
    accepts_dit_email_marketing,
    modified_at=None,
    **kwargs,
) -> bool:
    """
    Update consent preferences.
    """
    try:
        consent.update_consent(
            email_address,
            accepts_dit_email_marketing,
            modified_at=modified_at,
            **kwargs,
        )
        return True
    except requests.exceptions.RequestException as request_error:
        logger.warning('Retrying updating contact consent')
        raise RetryError(request_error)
    except (APIBadGatewayException, ImproperlyConfigured, Exception) as exec_info:
        logger.warning(
            'Unable to update contact consent',
            exc_info=exec_info,
            stack_info=True,
        )
        return False


def schedule_automatic_contact_archive(limit=1000, simulate=False):
    job = job_scheduler(
        function=automatic_contact_archive,
        function_args=(
            limit,
            simulate,
        ),
        max_retries=3,
        queue_name=LONG_RUNNING_QUEUE,
        job_timeout=HALF_DAY_IN_SECONDS,
    )
    logger.info(
        f'Task {job.id} automatic_contact_archive',
    )
    return job


def automatic_contact_archive(limit=1000, simulate=False):
    """
    Archive inactive contacts.
    """
    with advisory_lock('automatic_contact_archive', wait=False) as acquired:

        if not acquired:
            logger.info('Another instance of this task is already running.')
            return

        archive_count = _automatic_contact_archive(limit=limit, simulate=simulate)
        realtime_message = (
            f'datahub.company.tasks.automatic_contact_archive archived: {archive_count}'
        )
        if simulate:
            realtime_message = f'[SIMULATE] {realtime_message}'
        send_realtime_message(realtime_message)


def ingest_contact_consent_data():
    with advisory_lock('ingest_contact_consent_data', wait=False) as acquired:

        if not acquired:
            logger.info(
                'Another instance of this ingest_contact_consent_data task is already running.',
            )
            return

        task = ContactConsentIngestionTask()
        task.ingest()


env = environ.Env()
REGION = env('AWS_DEFAULT_REGION', default='eu-west-2')
BUCKET = f"data-flow-bucket-{env('ENVIRONMENT', default='')}"
PREFIX = 'data-flow/exports/'
CONSENT_PREFIX = f'{PREFIX}MergeConsentsPipeline/'


class ContactConsentIngestionTask:

    def _list_objects(self, client, bucket_name, prefix):
        """Returns a list all objects with specified prefix."""
        response = client.list_objects(
            Bucket=bucket_name,
            Prefix=prefix,
        )
        # Get the list of files, oldest first. Process in that order, so any changes in newer
        # files take precedence
        sorted_files = sorted(
            [object for object in response.get('Contents', {})],
            key=lambda x: x['LastModified'],
            reverse=False,
        )
        return [file['Key'] for file in sorted_files]

    def ingest(self):
        logger.info('Checking for new Contact Consent data files')
        s3_client = get_s3_client(REGION)
        file_keys = self._list_objects(s3_client, BUCKET, CONSENT_PREFIX)
        if len(file_keys) == 0:
            logger.info('No files found in bucket %s matching prefix %s', BUCKET, CONSENT_PREFIX)
            return
        for file_key in file_keys:
            self.sync_file_with_database(s3_client, file_key)
            self.delete_file(s3_client, file_key)

    def sync_file_with_database(self, client, file_key):
        logger.info('Syncing file %s', file_key)
        path = f's3://{BUCKET}/{file_key}'

        with open(
            path,
            'r',
            transport_params={
                'client': client,
            },
        ) as s3_file:
            i = 0
            for line in s3_file:
                i = i + 1
                if (i) % (10 ** min((max((math.floor(math.log10(i))), 2)), 6)) == 0:
                    logger.info('Processed %s rows from %s', i, path)
                consent_row = json.loads(line)
                if 'email' not in consent_row or 'consents' not in consent_row:
                    continue

                email = consent_row['email']
                matching_contact = Contact.objects.filter(email=email).first()

                if not matching_contact:
                    logger.debug('Email %s has no matching datahub contact', email)
                    continue

                last_modified = (
                    consent_row['last_modified'] if 'last_modified' in consent_row else None
                )

                update_row = False
                if matching_contact.consent_data_last_modified is None or last_modified is None:
                    update_row = True
                # to avoid issues with different source system time formats, just compare on the
                # date portion
                elif (
                    parser.parse(last_modified).date()
                    > matching_contact.consent_data_last_modified.date()
                ):
                    update_row = True

                if not update_row:
                    logger.debug(
                        'Email %s consent data has not been updated in the latest file',
                        email,
                    )
                    continue
                if settings.ENABLE_CONTACT_CONSENT_INGEST:
                    matching_contact.consent_data = consent_row['consents']
                    matching_contact.consent_data_last_modified = (
                        last_modified if last_modified else datetime.datetime.now()
                    )
                    matching_contact.save()

                    logger.debug('Updated consents for email %s', email)
                else:
                    logger.info(
                        'Email %s would have consent data updated, but setting is disabled',
                        email,
                    )

            logger.info('Finished processing total %s rows from %s', i, path)

    def delete_file(self, client, file_key):
        logger.info('Deleting file %s', file_key)
        client.delete_object(Bucket=BUCKET, Key=file_key)

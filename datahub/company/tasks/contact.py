import json
import logging

import boto3
import environ
import requests

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django_pglocks import advisory_lock

from smart_open import open

from datahub.company import consent
from datahub.company.models import Contact
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
            f'Record was automatically archived due to the company '
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
    with advisory_lock('consent_import', wait=False) as acquired:

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

    def get_s3_client(self):

        if settings.S3_LOCAL_ENDPOINT_URL:
            logger.debug('using local S3 endpoint %s', settings.S3_LOCAL_ENDPOINT_URL)
            return boto3.client('s3', REGION, endpoint_url=settings.S3_LOCAL_ENDPOINT_URL)

        return boto3.client('s3', REGION)

    def _list_objects(self, bucket_name, prefix):
        """Returns a list all objects with specified prefix."""
        s3_client = self.get_s3_client()
        response = s3_client.list_objects(
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
        file_keys = self._list_objects(BUCKET, CONSENT_PREFIX)
        if len(file_keys) == 0:
            logger.info('No files found in bucket %s matching prefix %s', BUCKET, CONSENT_PREFIX)
            return
        for file_key in file_keys:
            self.sync_file_with_database(file_key)
            self.delete_file(file_key)

    def sync_file_with_database(self, file_key):
        logger.info('Syncing file %s', file_key)
        path = f's3://{BUCKET}/{file_key}'

        with open(path) as s3_file:
            for line in s3_file:
                consent_row = json.loads(line)
                if 'email' not in consent_row or 'consents' not in consent_row:
                    continue
                email = consent_row['email']
                matching_contact = Contact.objects.filter(email=email).first()
                if not matching_contact:
                    logger.info('Email %s has no matching datahub contact', email)
                    continue

                matching_contact.consent_data = consent_row['consents']
                matching_contact.save()

                logger.info('Updated consents for email %s', email)

    def delete_file(self, file_key):
        logger.info('Deleting file %s', file_key)
        s3_client = self.get_s3_client()
        s3_client.delete_object(Bucket=BUCKET, Key=file_key)

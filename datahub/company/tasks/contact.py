import datetime
import json
import logging
import math
from typing import List

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

    def _log_at_interval(self, index: int, message: str):
        """
        Log in a way that is suitable for both small and large datasets. Initially
        a log info entry will be written every 100 rows, then increasing in frequency
        to every 1000, 10000, 100000 up to every million
        """
        if (index) % (10 ** min((max((math.floor(math.log10(index))), 2)), 6)) == 0:
            logger.info(message)

    def ingest(self):
        logger.info('Checking for new contact consent data files')
        s3_client = get_s3_client(REGION)
        file_keys = self._list_objects(s3_client, BUCKET, CONSENT_PREFIX)
        if len(file_keys) == 0:
            logger.info(
                'No contact consent files found in bucket %s matching prefix %s',
                BUCKET,
                CONSENT_PREFIX,
            )
            return

        for file_key in file_keys:
            try:
                self.sync_file_with_database(s3_client, file_key)
                self.delete_file(s3_client, file_key)
            except Exception as exc:
                logger.exception(
                    f'Error ingesting contact consent file {file_key}',
                    stack_info=True,
                )
                raise exc

    def get_grouped_contacts(self) -> dict[str, List[Contact]]:
        contacts_qs = Contact.objects.all()
        contact_dict = {}
        for d in contacts_qs:
            contact_dict.setdefault(d.email, []).append(d)
        return contact_dict

    def should_update_contact(self, contact: Contact, consent_row):

        last_modified = consent_row['last_modified'] if 'last_modified' in consent_row else None

        if contact.consent_data_last_modified is None or last_modified is None:
            return True

        # To avoid issues with different source system time formats, just compare on
        # the date portion
        if parser.parse(last_modified).date() > contact.consent_data_last_modified.date():
            return True
        return False

    def sync_file_with_database(self, client, file_key):
        logger.info(
            'Syncing contact consent file %s with datahub contacts',
            file_key,
        )
        path = f's3://{BUCKET}/{file_key}'

        contact_dict = self.get_grouped_contacts()

        if not contact_dict:
            logger.info('No contacts were found')
            return

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

                self._log_at_interval(i, f'Processed {i} rows from {path}')

                consent_row = json.loads(line)
                if 'email' not in consent_row or 'consents' not in consent_row:
                    logger.info(
                        'Row %s does not contain required consent data to process, skipping',
                        i,
                    )
                    continue

                email = consent_row['email']

                if not email:
                    logger.debug('Row %s has no email', i)
                    continue

                matching_contacts = contact_dict.get(email)

                if not matching_contacts or len(matching_contacts) == 0:
                    logger.debug(
                        'Email %s in contact consent file has no matching datahub contacts',
                        email,
                    )
                    continue

                for contact in matching_contacts:

                    if not self.should_update_contact(contact, consent_row):
                        logger.info(
                            'Email %s does not need to be updated',
                            email,
                        )
                        continue

                    if not settings.ENABLE_CONTACT_CONSENT_INGEST:
                        logger.info(
                            'Email %s would have consent data updated, but setting is disabled',
                            email,
                        )
                        continue

                    contact.consent_data = consent_row['consents']
                    contact.consent_data_last_modified = (
                        consent_row['last_modified']
                        if 'last_modified' in consent_row and consent_row['last_modified']
                        else datetime.datetime.now()
                    )

                    # We don't need to trigger sync related data signals, use an update
                    # instead of a save
                    Contact.objects.filter(id=contact.id).update(
                        consent_data=contact.consent_data,
                        consent_data_last_modified=contact.consent_data_last_modified,
                    )
                    logger.info('Updated contact consent data for email %s in row %s', email, i)

            logger.info(
                'Finished processing total %s rows for contact consent from file %s',
                i,
                path,
            )

    def delete_file(self, client, file_key):
        logger.info('Deleting contact consent file %s', file_key)
        client.delete_object(Bucket=BUCKET, Key=file_key)
        logger.info('Successfully deleted contact consent file %s', file_key)

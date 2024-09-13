import json
import logging

import requests
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django_pglocks import advisory_lock

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
    ).prefetch_related("company")[:limit]

    for contact in contacts_to_be_archived:
        message = f"Automatically archived contact: {contact.id}"
        if simulate:
            logger.info(f"[SIMULATION] {message}")
            continue
        contact.archived = True
        contact.archived_reason = (
            f"Record was automatically archived due to the company "
            f'"{contact.company.name}" being archived'
        )
        contact.archived_on = timezone.now()
        contact.save(
            update_fields=[
                "archived",
                "archived_reason",
                "archived_on",
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
        f"Task {job.id} update_contact_consent",
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
        logger.warning("Retrying updating contact consent")
        raise RetryError(request_error)
    except (APIBadGatewayException, ImproperlyConfigured, Exception) as exec_info:
        logger.warning(
            "Unable to update contact consent",
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
        f"Task {job.id} automatic_contact_archive",
    )
    return job


def automatic_contact_archive(limit=1000, simulate=False):
    """
    Archive inactive contacts.
    """
    with advisory_lock("automatic_contact_archive", wait=False) as acquired:

        if not acquired:
            logger.info("Another instance of this task is already running.")
            return

        archive_count = _automatic_contact_archive(limit=limit, simulate=simulate)
        realtime_message = (
            f"datahub.company.tasks.automatic_contact_archive archived: {archive_count}"
        )
        if simulate:
            realtime_message = f"[SIMULATE] {realtime_message}"
        send_realtime_message(realtime_message)


def _get_consent_files(s3_bucket):
    # get list of consent files from the bucket, ordered by date ascending
    files = s3_bucket.objects.filter(Prefix="consent")
    sorted_files = sorted(files, key=lambda x: x.last_modified, reverse=False)
    return [f"s3://{file.bucket_name}/{file.key}" for file in sorted_files]


def ingest_consent():
    s3_client = None
    s3_resource = None
    s3_bucket = None
    files = _get_consent_files(s3_bucket)
    for file in files:
        pass


from smart_open import open as smart_open


def _ingest_consent_file(file):
    logger.info("Ingesting consent from file %s", file)
    with smart_open(
        file,
        mode="r",
        encoding="UTF-8",
        transport_params={
            "client": None,
        },
    ) as input_file:
        for line in input_file:
            contact_json = json.loads(line)
            contact = Contact.objects.filter(id=contact_json['contactid']).first()
            if contact is None:
                logger.info("Contact id %s does not exist in datahub", contact_json['contactid'])
                continue
            pass

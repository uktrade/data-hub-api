import socket

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import F, Max, Q
from redis import Redis
from redis_rate_limit import RateLimit

from datahub.company.models import Company
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.dnb_api.utils import (
    get_company,
    update_company_from_dnb,
)

logger = get_task_logger(__name__)


def _sync_company_with_dnb(
    company_id,
    fields_to_update,
    update_descriptor,
):
    dh_company = Company.objects.get(id=company_id)
    dnb_company = get_company(dh_company.duns_number)

    update_company_from_dnb(
        dh_company,
        dnb_company,
        fields_to_update=fields_to_update,
        update_descriptor=update_descriptor,
    )


def sync_company_with_dnb(
    company_id,
    fields_to_update=None,
    update_descriptor=None,
):
    """
    Sync a company record with data sourced from DNB. This task will interact with dnb-service to
    get the latest data for the company.

    `company_id` identifies the company record to sync and `fields_to_update` defines an iterable
    of company serializer fields that should be updated - if it is None, all fields will be synced.
    `update_descriptor` can be specified and will be embedded within the reversion comment for
    the new company version.
    """
    if not update_descriptor:
        update_descriptor = f'rq:sync_company_with_dnb:{company_id}'
    _sync_company_with_dnb(company_id, fields_to_update, update_descriptor)


def schedule_sync_company_with_dnb_rate_limited(
    company_id,
    fields_to_update=None,
    update_descriptor=None,
    simulate=False,
):
    # rate_limit=1,  # Run this task at most one per worker per second
    job = job_scheduler(
        function=sync_company_with_dnb_rate_limited,
        function_args=(
            company_id,
            fields_to_update,
            update_descriptor,
            simulate,
        ),
        max_retries=3,
        queue_name=LONG_RUNNING_QUEUE,
        job_timeout=HALF_DAY_IN_SECONDS,
        retry_backoff=60,
    )
    logger.info(
        f'Task {job.id} sync_company_with_dnb_rate_limited',
    )
    return job


def sync_company_with_dnb_rate_limited(
    company_id,
    fields_to_update=None,
    update_descriptor=None,
    simulate=False,
):
    """
    A rate limited wrapper around the sync_company_with_dnb task. This task
    can be used for bulk tasks to ensure that we do not exceed our agreed
    rate limit with D&B.
    """
    message = f'Syncing dnb-linked company "{company_id}"'
    if simulate:
        logger.info(f'[SIMULATION] {message} Succeeded')
        return

    try:
        # TODO: See what this should be s I am not able to find the documentation
        with RateLimit(
            resource='sync_company_with_dnb_rate_limited',
            client=socket.gethostbyaddr(socket.gethostname()),
            max_requests=4,
            expire=1,
            redis_pool=Redis.from_url(settings.REDIS_BASE_URL),
        ):
            sync_company_with_dnb(
                company_id=company_id,
                fields_to_update=fields_to_update,
                update_descriptor=update_descriptor,
            )
    except Exception:
        logger.warning(f'{message} Failed')
        raise

    logger.info(f'{message} Succeeded')


@shared_task(
    bind=True,
    acks_late=True,
    priority=9,
    queue='long-running',
)
def sync_outdated_companies_with_dnb(
    self,
    dnb_modified_on_before,
    fields_to_update=None,
    limit=100,
    simulate=True,
):
    """
    Sync company records with data sourced from DNB which are determined as outdated.
    This task will filter dnb-matched companies which have a `dnb_modified_on` date which is before
    `dnb_modified_on_before` and will then interact with dnb-service to get the latest data to sync
    these companies.
    """
    company_ids = Company.objects.filter(
        Q(dnb_modified_on__lte=dnb_modified_on_before) | Q(dnb_modified_on__isnull=True),
        duns_number__isnull=False,
    ).annotate(
        most_recent_interaction_date=Max('interactions__date'),
    ).order_by(
        F('most_recent_interaction_date').desc(nulls_last=True),
        'dnb_modified_on',
    ).values_list('id', flat=True)[:limit]

    for company_id in company_ids:
        schedule_sync_company_with_dnb_rate_limited(
            company_id=company_id,
            fields_to_update=fields_to_update,
            update_descriptor=f'rq:sync_outdated_companies_with_dnb:{self.request.id}',
            simulate=simulate,
        )

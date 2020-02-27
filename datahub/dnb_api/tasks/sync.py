from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import F, Max, Q
from rest_framework.status import is_server_error

from datahub.company.models import Company
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceTimeoutError,
    get_company,
    update_company_from_dnb,
)

logger = get_task_logger(__name__)


def _sync_company_with_dnb(
    company_id,
    fields_to_update,
    task,
    update_descriptor,
    retry_failures=True,
):
    dh_company = Company.objects.get(id=company_id)

    try:
        dnb_company = get_company(dh_company.duns_number)
    except DNBServiceError as exc:
        if is_server_error(exc.status_code) and retry_failures:
            raise task.retry(exc=exc, countdown=60)
        raise
    except (DNBServiceConnectionError, DNBServiceTimeoutError) as exc:
        if retry_failures:
            raise task.retry(exc=exc, countdown=60)
        raise

    update_company_from_dnb(
        dh_company,
        dnb_company,
        fields_to_update=fields_to_update,
        update_descriptor=update_descriptor,
    )


@shared_task(
    bind=True,
    acks_late=True,
    priority=9,
    max_retries=3,
)
def sync_company_with_dnb(
    self,
    company_id,
    fields_to_update=None,
    update_descriptor=None,
    retry_failures=True,
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
        update_descriptor = f'celery:sync_company_with_dnb:{self.request.id}'
    _sync_company_with_dnb(company_id, fields_to_update, self, update_descriptor, retry_failures)


@shared_task(
    bind=True,
    acks_late=True,
    priority=9,
    max_retries=3,
    rate_limit=1,  # Run this task at most once per worker per second
    queue='long-running',
)
def sync_company_with_dnb_rate_limited(
    self,
    company_id,
    fields_to_update=None,
    update_descriptor=None,
    retry_failures=True,
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
        sync_company_with_dnb.apply(
            kwargs={
                'company_id': company_id,
                'fields_to_update': fields_to_update,
                'update_descriptor': update_descriptor,
                'retry_failures': retry_failures,
            },
            throw=True,
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
        sync_company_with_dnb_rate_limited.apply_async(
            kwargs={
                'company_id': company_id,
                'fields_to_update': fields_to_update,
                'update_descriptor': 'celery:sync_outdated_companies_with_dnb:{self.request.id}',
                'simulate': simulate,
                'retry_failures': False,
            },
        )

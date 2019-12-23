from datetime import datetime, time, timedelta

from celery import shared_task
from celery.result import ResultSet
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils.timezone import now
from django_pglocks import advisory_lock
from rest_framework.status import is_server_error

from datahub.company.models import Company
from datahub.core.utils import log_to_sentry
from datahub.dnb_api.constants import FEATURE_FLAG_DNB_COMPANY_UPDATES
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceTimeoutError,
    format_dnb_company,
    get_company,
    get_company_update_page,
    update_company_from_dnb,
)
from datahub.feature_flag.utils import is_feature_flag_active

logger = get_task_logger(__name__)


def _sync_company_with_dnb(company_id, fields_to_update, task, update_descriptor):
    dh_company = Company.objects.get(id=company_id)

    try:
        dnb_company = get_company(dh_company.duns_number)
    except DNBServiceError as exc:
        if is_server_error(exc.status_code):
            raise task.retry(exc=exc, countdown=60)
        raise
    except (DNBServiceConnectionError, DNBServiceTimeoutError) as exc:
        raise task.retry(exc=exc, countdown=60)

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
def sync_company_with_dnb(self, company_id, fields_to_update=None, update_descriptor=None):
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
    _sync_company_with_dnb(company_id, fields_to_update, self, update_descriptor)


def _record_audit(update_results, producer_task, start_time):
    """
    Record an audit log for the get_company_updates task which expresses the number
    of companies successfully updates, failures, ids of companies updated, celery
    task info and start/end times.
    """
    audit = {
        'success_count': 0,
        'failure_count': 0,
        'updated_company_ids': [],
        'producer_task_id': producer_task.request.id,
        'start_time': start_time.isoformat(),
        'end_time': now().isoformat(),
    }
    for result in update_results:
        if result.successful():
            audit['success_count'] += 1
            audit['updated_company_ids'].append(result.result)
        else:
            audit['failure_count'] += 1
    log_to_sentry('get_company_updates task completed.', extra=audit)


def _get_company_updates_from_api(last_updated_after, next_page, task):
    try:
        return get_company_update_page(last_updated_after, next_page)

    except DNBServiceError as exc:
        if is_server_error(exc.status_code):
            raise task.retry(exc=exc, countdown=60)
        raise

    except (DNBServiceConnectionError, DNBServiceTimeoutError) as exc:
        raise task.retry(exc=exc, countdown=60)


def _get_company_updates(task, last_updated_after, fields_to_update):
    yesterday = now() - timedelta(days=1)
    midnight_yesterday = datetime.combine(yesterday, time.min)
    last_updated_after = last_updated_after or midnight_yesterday.isoformat()
    next_page = None
    updates_remaining = settings.DNB_AUTOMATIC_UPDATE_LIMIT
    update_results = []
    start_time = now()
    logger.info('Started get_company_updates task')
    update_descriptor = f'celery:get_company_updates:{task.request.id}'

    while True:

        response = _get_company_updates_from_api(last_updated_after, next_page, task)
        dnb_company_updates = response.get('results', [])

        dnb_company_updates = dnb_company_updates[:updates_remaining]

        # Spawn tasks that update Data Hub companies
        for data in dnb_company_updates:
            result = update_company_from_dnb_data.apply_async(
                args=(data,),
                kwargs={
                    'fields_to_update': fields_to_update,
                    'update_descriptor': update_descriptor,
                },
            )
            update_results.append(result)

        if updates_remaining is not None:
            updates_remaining -= len(dnb_company_updates)
            if updates_remaining <= 0:
                break

        next_page = response.get('next')
        if next_page is None:
            break

    # Wait for all update tasks to finish...
    ResultSet(results=update_results).join(
        propagate=False,
        disable_sync_subtasks=False,
    )
    _record_audit(update_results, task, start_time)
    logger.info('Finished get_company_updates task')


@shared_task(
    bind=True,
    acks_late=True,
    priority=9,
    max_retries=3,
    queue='long-running',
)
def get_company_updates(self, last_updated_after=None, fields_to_update=None):
    """
    Gets the lastest updates for D&B companies from dnb-service.

    The `dnb-service` exposes these updates as a cursor-paginated list. This
    task goes through the pages and spawns tasks that update the records in
    Data Hub.
    """
    # TODO: remove this feature flag after a reasonable period after going live
    # with unlimited company updates
    if not is_feature_flag_active(FEATURE_FLAG_DNB_COMPANY_UPDATES):
        logger.info(
            f'Feature flag "{FEATURE_FLAG_DNB_COMPANY_UPDATES}" is not active, exiting.',
        )
        return

    with advisory_lock('get_company_updates', wait=False) as acquired:

        if not acquired:
            logger.info('Another instance of this task is already running.')
            return

        _get_company_updates(self, last_updated_after, fields_to_update)


@shared_task(
    acks_late=True,
    priority=9,
)
def update_company_from_dnb_data(dnb_company_data, fields_to_update=None, update_descriptor=None):
    """
    Update the company with the latest data from dnb-service. This task should be called
    when some other logic interacts with dnb-service to get the company data as the task itself
    will not interact with dnb-service.
    """
    dnb_company = format_dnb_company(dnb_company_data)
    duns_number = dnb_company['duns_number']
    logger.info(f'Updating company with duns_number: {duns_number}')

    try:
        dh_company = Company.objects.get(duns_number=duns_number)
    except Company.DoesNotExist:
        logger.error(
            'Company matching duns_number was not found',
            extra={
                'duns_number': duns_number,
                'dnb_company': dnb_company,
            },
        )
        raise

    if not update_descriptor:
        update_descriptor = 'celery:company_update'

    update_company_from_dnb(
        dh_company,
        dnb_company,
        fields_to_update=fields_to_update,
        update_descriptor=update_descriptor,
    )
    return str(dh_company.pk)

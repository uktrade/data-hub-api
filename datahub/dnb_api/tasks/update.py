from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils.timezone import now
from django_pglocks import advisory_lock
from rq.exceptions import NoSuchJobError

from datahub.company.models import Company
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS, THIRTY_MINUTES_IN_SECONDS
from datahub.core.queues.errors import RetryError
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import DataHubScheduler, LONG_RUNNING_QUEUE
from datahub.core.realtime_messaging import send_realtime_message
from datahub.core.utils import log_to_sentry
from datahub.dnb_api.tasks.sync import logger
from datahub.dnb_api.utils import (
    format_dnb_company,
    get_company_update_page,
    update_company_from_dnb,
)


def schedule_record_audit(job_ids, start_time):
    """
    Check all jobs every 30 minutes for the span of 4 hours
    and then fail if not finished
    """
    max_retries = 8
    job = job_scheduler(
        function=record_audit,
        function_args=(
            job_ids,
            start_time,
        ),
        max_retries=max_retries,
        queue_name=LONG_RUNNING_QUEUE,
        job_timeout=HALF_DAY_IN_SECONDS,
        retry_intervals=[THIRTY_MINUTES_IN_SECONDS] * max_retries,
    )
    logger.info(
        f'Task {job.id} schedule_get_company_updates',
    )
    return job


def record_audit(job_ids, start_time):
    """
    Record an audit log for the get_company_updates task which expresses the number
    of companies successfully updates, failures, job_count and RQ
    task info and start/end times.
    """
    audit = {
        'success_count': 0,
        'failure_count': 0,
        'job_count': len(job_ids),
        'start_time': start_time.isoformat(),
        'end_time': now().isoformat(),
    }
    scheduler = DataHubScheduler()
    for job_id in job_ids:
        try:
            job = scheduler.job(job_id=job_id)
            if job.is_finished:
                audit['success_count'] += 1
            elif job.is_failed:
                audit['failure_count'] += 1
            else:
                raise RetryError(f'{job_id} has a {job.get_status(refresh=False)}')
        except NoSuchJobError:
            # Job success ttl expired within 500s assumed therefore this succeeded
            audit['success_count'] += 1
    audit['end_time'] = now().isoformat()
    log_to_sentry('get_company_updates task completed.', extra=audit)
    success_count, failure_count = audit['success_count'], audit['failure_count']
    realtime_message = (
        f'datahub.dnb_api.tasks.update.get_company_updates updated: {success_count}; '
        f'failed to update: {failure_count}'
    )
    send_realtime_message(realtime_message)


def _get_company_updates(last_updated_after, fields_to_update):
    yesterday = now() - timedelta(days=1)
    midnight_yesterday = datetime.combine(yesterday, time.min)
    last_updated_after = last_updated_after or midnight_yesterday.isoformat()
    next_page = None
    updates_remaining = settings.DNB_AUTOMATIC_UPDATE_LIMIT
    job_ids = []
    start_time = now()
    logger.info('Started get_company_updates task')
    update_descriptor = f'rq:get_company_updates:{start_time}'

    while True:

        response = get_company_update_page(last_updated_after, next_page)
        dnb_company_updates = response.get('results', [])

        dnb_company_updates = dnb_company_updates[:updates_remaining]

        # Spawn tasks that update Data Hub companies
        for data in dnb_company_updates:
            job = schedule_update_company_from_dnb_data(
                dnb_company_data=data,
                fields_to_update=fields_to_update,
                update_descriptor=update_descriptor,
            )
            job_ids.append(job.id)

        if updates_remaining is not None:
            updates_remaining -= len(dnb_company_updates)
            if updates_remaining <= 0:
                break

        next_page = response.get('next')
        if next_page is None:
            break

    # Wait for all update tasks to finish...
    schedule_record_audit(job_ids, start_time)
    logger.info('Finished scheduling get_company_updates task')


def schedule_get_company_updates(
    last_updated_after=None,
    fields_to_update=None,
):
    job = job_scheduler(
        function=get_company_updates,
        function_args=(
            last_updated_after,
            fields_to_update,
        ),
        max_retries=3,
        queue_name=LONG_RUNNING_QUEUE,
        job_timeout=HALF_DAY_IN_SECONDS,
    )
    logger.info(
        f'Task {job.id} schedule_get_company_updates',
    )
    return job


def get_company_updates(last_updated_after=None, fields_to_update=None):
    """
    Gets the lastest updates for D&B companies from dnb-service.

    The `dnb-service` exposes these updates as a cursor-paginated list. This
    task goes through the pages and spawns tasks that update the records in
    Data Hub.
    """
    with advisory_lock('get_company_updates', wait=False) as acquired:

        if not acquired:
            logger.info('Another instance of this task is already running.')
            return

        _get_company_updates(last_updated_after, fields_to_update)


def schedule_update_company_from_dnb_data(
    dnb_company_data,
    fields_to_update=None,
    update_descriptor=None,
):
    job = job_scheduler(
        function=update_company_from_dnb_data,
        function_args=(
            dnb_company_data,
            fields_to_update,
            update_descriptor,
        ),
    )
    logger.info(
        f'Task {job.id} update_company_from_dnb_data',
    )
    return job


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

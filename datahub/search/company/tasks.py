import logging

from datahub.company.models.company import Company
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.search.sync_object import sync_related_objects_async

logger = logging.getLogger(__name__)


def schedule_sync_investment_projects_of_subsidiary_companies(company, original_modified_on):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=sync_investment_projects_of_subsidiary_companies,
        function_kwargs={
            'company': company,
            'original_modified_on': original_modified_on,
        },
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
    )
    logger.info(
        f'Task {job.id} schedule_sync_investment_projects_of_subsidiary_companies '
        f'scheduled company {company}',
    )
    return job


def sync_investment_projects_of_subsidiary_companies(company, original_modified_on):
    """When the one list account owner has changed this should be updated on all related
    investment projects for all subsidiary companies.
    """
    # Avoid race condition. Data currently in database should have been modified by save method
    # after original_modified_on, if not fail so scheduler can try again.
    current = Company.objects.get(pk=company.pk)
    if original_modified_on >= current.modified_on:
        # Fail job and retry.
        try:
            raise Exception('Race condition in sync_investment_projects_of_subsidiary_companies')
        except Exception as exception:
            exception.extra_info = f'Company id: {company.id}, ' + \
                f'Company modified_on: {company.modified_on}, ' + \
                f'original_modified_on: {original_modified_on}.'
            raise

    subsidiary_companies = Company.objects.filter(
        global_headquarters_id=company.id,
    )

    for subsidiary_company in subsidiary_companies:
        sync_related_objects_async(subsidiary_company, 'investor_investment_projects')

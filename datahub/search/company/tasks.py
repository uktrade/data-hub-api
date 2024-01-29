import logging

from datahub.company.models.company import Company
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.search.sync_object import sync_related_objects_async

logger = logging.getLogger(__name__)


def schedule_sync_investment_projects_of_subsidiary_companies(company):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=sync_investment_projects_of_subsidiary_companies,
        function_kwargs={
            'company': company,
        },
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=3,
    )
    logger.info(
        f'Task {job.id} schedule_sync_investment_projects_of_subsidiary_companies '
        f'scheduled company {company}',
    )
    return job


def sync_investment_projects_of_subsidiary_companies(company):
    """
    When the one list account owner has changed this should be updated on all related
    investment projects for all subsidiary companies.
    """
    subsidiary_companies = Company.objects.filter(
        global_headquarters_id=company.id,
    )

    for subsidiary_company in subsidiary_companies:
        sync_related_objects_async(subsidiary_company, 'investor_investment_projects')

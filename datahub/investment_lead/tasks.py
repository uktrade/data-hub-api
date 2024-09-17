import logging

from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.investment_lead.services import process_eyb_lead

logger = logging.getLogger(__name__)


def schedule_process_eyb_leads(eyb_leads):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=process_eyb_leads,
        function_kwargs={
            'eyb_leads': eyb_leads,
        },
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
    )
    logger.info(
        f'Task {job.id} schedule_process_eyb_leads '
        f'scheduled company {eyb_leads}',
    )
    return job


def process_eyb_leads(eyb_leads, modified_on):
    for eyb_lead in eyb_leads:
        # Check if recently updated
        process_eyb_lead(eyb_lead)

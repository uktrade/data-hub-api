import logging

from celery import shared_task

from django.core.management import call_command

from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE

logger = logging.getLogger(__name__)


def schedule_update_company_export_potential_from_csv(csv_file_path='', simulate=True):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=update_company_export_potential_from_csv,
        function_kwargs={
            'csv_file_path': csv_file_path,
            'simulate': simulate,
        },
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=3,
    )
    logger.info(
        f'Task {job.id} update_company_export_potential_from_csv '
        f'scheduled to consume {csv_file_path} and simulate set to {simulate}',
    )
    return job


@shared_task
def update_company_export_potential_from_csv(csv_file_path, simulate=False):
    """
    A Celery task to update company export potential from a CSV file.

    :param csv_file_path: Path to the CSV file with company numbers and export potential scores.
    :param simulate: If True, run the command in simulate mode without changing the database.
    """
    call_command(
        'update_company_export_potential',
        csv_file=csv_file_path,
        simulate=simulate,
    )

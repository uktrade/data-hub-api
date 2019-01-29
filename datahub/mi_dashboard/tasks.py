from time import perf_counter

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django_pglocks import advisory_lock

from datahub.mi_dashboard.pipelines import run_mi_investment_project_etl_pipeline

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    acks_late=True,
    priority=7,
    max_retries=5,
    autoretry_for=(Exception,),
    retry_backoff=60,
    queue='long-running',
)
def mi_investment_project_etl_pipeline(self):
    """
    Completes MI dashboard feed.
    """
    with advisory_lock(f'leeloo-mi_investment_project_etl_pipeline', wait=False) as lock_held:
        if not lock_held:
            logger.warning(
                f'Another mi_dashboard_feed task is in progress. Aborting...',
            )
            return

        logger.info('Started MI dashboard feed.')

        start_time = perf_counter()
        updated, created = run_mi_investment_project_etl_pipeline()
        elapsed_time = perf_counter() - start_time
        if elapsed_time > settings.MI_FDI_DASHBOARD_TASK_DURATION_WARNING_THRESHOLD:
            logger.warning((
                'The mi_investment_project_etl_pipeline task took a long time '
                '({elapsed_time:.2f} seconds).'
            ))

        logger.info(f'Updated "{updated}" and created "{created}" investment projects.')

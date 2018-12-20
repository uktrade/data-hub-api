from celery import shared_task
from celery.utils.log import get_task_logger
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
def mi_investment_project_etl_pipeline(self, financial_year: str):
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

        updated, created = run_mi_investment_project_etl_pipeline(financial_year)

        logger.info(f'Updated "{updated}" and created "{created}" investment projects.')

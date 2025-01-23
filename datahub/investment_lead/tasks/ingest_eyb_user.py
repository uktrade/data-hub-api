import logging

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.constants import DATA_FLOW_EXPORTS_PREFIX
from datahub.investment_lead.serializers import CreateEYBLeadUserSerializer
from datahub.investment_lead.services import link_leads_to_companies
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BaseEYBIdentificationTask,
    BaseEYBIngestionTask,
)
from datahub.investment_lead.tasks.ingest_eyb_marketing import eyb_marketing_identification_task


USER_PREFIX = f'{DATA_FLOW_EXPORTS_PREFIX}DirectoryExpandYourBusinessUserDataPipeline/'


logger = logging.getLogger(__name__)


def eyb_user_identification_task() -> None:
    logger.info('EYB user identification task started...')
    identification_task = EYBUserIdentificationTask(prefix=USER_PREFIX)
    identification_task.identify_new_objects(eyb_user_ingestion_task)
    logger.info('EYB user identification task finished.')


class EYBUserIdentificationTask(BaseEYBIdentificationTask):
    """Class to identify new EYB user objects and determine if they should be ingested."""


def eyb_user_ingestion_task(object_key: str) -> None:
    logger.info('EYB user ingestion task started...')
    ingestion_task = EYBUserIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=USER_PREFIX),
        serializer_class=CreateEYBLeadUserSerializer,
    )
    ingestion_task.ingest_object()
    logger.info('EYB user ingestion task finished.')

    link_leads_to_companies()
    logger.info('Linked leads to companies')

    # Chain next job (EYB marketing object identification);
    # This avoids creating duplicate EYB leads when ingesting different components simultaneously
    job_scheduler(
        function=eyb_marketing_identification_task,
        description='Identify new EYB marketing objects',
    )
    logger.info('EYB user ingestion task has scheduled EYB marketing identification task')


class EYBUserIngestionTask(BaseEYBIngestionTask):
    """Class to ingest a specific EYB user object from S3."""

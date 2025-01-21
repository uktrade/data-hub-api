import logging

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.constants import DATA_FLOW_EXPORTS_PREFIX
from datahub.investment_lead.serializers import CreateEYBLeadTriageSerializer
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BaseEYBIdentificationTask,
    BaseEYBIngestionTask,
)
from datahub.investment_lead.tasks.ingest_eyb_user import eyb_user_identification_task


TRIAGE_PREFIX = f'{DATA_FLOW_EXPORTS_PREFIX}DirectoryExpandYourBusinessTriageDataPipeline/'


logger = logging.getLogger(__name__)


def eyb_triage_identification_task() -> None:
    logger.info('EYB triage identification task started...')
    identification_task = EYBTriageIdentificationTask(prefix=TRIAGE_PREFIX)
    identification_task.identify_new_objects(eyb_triage_ingestion_task)
    logger.info('EYB triage identification task finished.')


class EYBTriageIdentificationTask(BaseEYBIdentificationTask):
    """Class to identify new EYB triage objects and determine if they should be ingested."""


def eyb_triage_ingestion_task(object_key: str) -> None:
    logger.info('EYB triage ingestion task started...')
    ingestion_task = EYBTriageIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=TRIAGE_PREFIX),
        serializer_class=CreateEYBLeadTriageSerializer,
    )
    ingestion_task.ingest_object()
    logger.info('EYB triage ingestion task finished.')

    # Chain next job (EYB user object identification);
    # This avoids creating duplicate EYB leads when ingesting different components simultaneously
    job_scheduler(
        function=eyb_user_identification_task,
        description='Identify new EYB user objects',
    )
    logger.info('EYB triage ingestion task has scheduled EYB user identification task')


class EYBTriageIngestionTask(BaseEYBIngestionTask):
    """Class to ingest a specific EYB triage object from S3."""

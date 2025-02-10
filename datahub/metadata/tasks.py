import logging

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import BaseObjectIdentificationTask, BaseObjectIngestionTask
from datahub.metadata.constants import POSTCODE_DATA_PREFIX


logger = logging.getLogger(__name__)


def postcode_data_identification_task() -> None:
    """Identifies the most recent file to be ingested and schedules a task to ingest it"""
    logger.info('Postcode data identification task started.')
    identification_task = PostcodeDataIndentificationTask(prefix=POSTCODE_DATA_PREFIX)
    identification_task.identify_new_objects(postcode_data_ingestion_task)
    logger.info('Postcode data identification task finished.')


def postcode_data_ingestion_task(object_key: str) -> None:
    """Ingest the given key (file) from S3"""
    logger.info(f'Postcode data ingestion task started for file {object_key}.')
    ingestion_task = PostcodeDataIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=POSTCODE_DATA_PREFIX),
    )
    ingestion_task.ingest_object()
    logger.info(f'Postcode data ingestion task finished for file {object_key}.')


class PostcodeDataIndentificationTask(BaseObjectIdentificationTask):
    pass


class PostcodeDataIngestionTask(BaseObjectIngestionTask):
    pass

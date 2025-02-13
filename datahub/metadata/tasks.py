import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import BaseObjectIdentificationTask, BaseObjectIngestionTask
from datahub.metadata.constants import POSTCODE_DATA_PREFIX
from datahub.metadata.models import PostcodeData


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

    existing_ids = []

    def _should_process_record(self, record: dict) -> bool:
        """Checks whether the record has already been ingested or not."""
        if not self.existing_ids:
            self.existing_ids = set(PostcodeData.objects.values_list(
                'postcode_data_id', flat=True))

        postcode_data_id = record.get('id')
        if postcode_data_id in self.existing_ids:
            logger.info(f'Record already exists for postcode_data_id: {postcode_data_id}')
            return False

        return True

    def _process_record(self, record: dict) -> None:
        """Processes a single record.
        Saves postcode data from the S3 bucket into `PostcodeData`
        """
        postcode_data_id = record.get('id')
        values = {
            'postcode_data_id': record.get('id'),
            'postcode': record.get('postcode', ''),
            'modified_on': record.get('modified_on', ''),
            'postcode_region': record.get('postcode_data_region', ''),
            'publication_date': record.get('publication_date'),
        }

        try:
            PostcodeData.objects.create(**values)
        except IntegrityError as error:
            logger.error(
                f'Error processing postcode data record, postcode_data_id: {postcode_data_id}. '
                f'Error: {error}',
            )
        except ValidationError as error:
            logger.error(
                'Got unexpected value for a field when processing postcode data record, '
                f'postcode_data_id: {postcode_data_id}. '
                f'Error: {error}',
            )

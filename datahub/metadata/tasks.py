import json
import logging

import smart_open

from datahub.core.queues.constants import THIRTY_MINUTES_IN_SECONDS
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import BaseObjectIdentificationTask, BaseObjectIngestionTask
from datahub.metadata.constants import POSTCODE_DATA_PREFIX
from datahub.metadata.models import PostcodeData

logger = logging.getLogger(__name__)


def postcode_data_identification_task() -> None:
    logger.info('Postcode data identification task started...')
    identification_task = PostcodeDataIdentificationTask(
        prefix=POSTCODE_DATA_PREFIX, 
        job_timeout=THIRTY_MINUTES_IN_SECONDS
    )
    identification_task.identify_new_objects(postcode_data_ingestion_task)
    logger.info('Postcode data identification task finished.')


class PostcodeDataIdentificationTask(BaseObjectIdentificationTask):
    """Class to identify new postcode data objects and determine if they should be ingested."""


def postcode_data_ingestion_task(object_key: str) -> None:
    logger.info('Postcode data ingestion task started...')
    ingestion_task = PostcodeDataIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=POSTCODE_DATA_PREFIX),
    )
    ingestion_task.ingest_object()
    logger.info('Postcode data ingestion task finished.')


class PostcodeDataIngestionTask(BaseObjectIngestionTask):
    """Class to ingest a postcode object from S3."""

    def __init__(
        self,
        object_key: str,
        s3_processor: S3ObjectProcessor,
    ) -> None:
        logger.info('Starting PostcodeDataIngestionTask initialisation.')
        super().__init__(object_key, s3_processor)
        self._existing_ids = set(PostcodeData.objects.values_list('id', flat=True))
        self._fields_to_update = PostcodeDataIngestionTask._fields_to_update()
        self._to_create = []
        self._to_update = []
        self._to_delete = []
        logger.info('Completed PostcodeDataIngestionTask initialisation.')

    def ingest_object(self) -> None:
        """Process all records in the object key specified when the class instance was created."""
        try:
            with smart_open.open(
                f's3://{self.s3_processor.bucket}/{self.object_key}',
                transport_params={'client': self.s3_processor.s3_client},
            ) as s3_object:
                logger.info('PostcodeDataIngestionTask: ingest_object.')
                all_file_ids = set()
                for line in s3_object:
                    jsn = json.loads(line)
                    object = PostcodeData(**jsn)
                    if not object.id:
                        continue
                    if object.id in self._existing_ids:
                        self._to_update.append(object)
                    else:
                        self._to_create.append(object)
                    all_file_ids.add(object.id)
                if len(all_file_ids) > 0:
                    self._to_delete = self._existing_ids - all_file_ids
                    PostcodeData.objects.bulk_create(self._to_create)
                    PostcodeData.objects.bulk_update(
                        self._to_update,
                        self._fields_to_update,
                    )
                    PostcodeData.objects.filter(id__in=self._to_delete).delete()
        except Exception as e:
            logger.error(f'An error occurred trying to process {self.object_key}: {e}')
            raise e
        self._log_ingestion_metrics()

    def _fields_to_update():
        fields = [field.name for field in PostcodeData._meta.get_fields()]
        fields.remove('id')
        return fields

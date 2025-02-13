import logging

from uuid import UUID

from rest_framework import serializers

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

    def __init__(
        self,
        object_key: str,
        s3_processor: S3ObjectProcessor,
        serializer_class: serializers.Serializer,
    ) -> None:
        self.serializer_class = serializer_class
        super().__init__(object_key, s3_processor)

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

    def _get_hashed_uuid(self, record: dict) -> str:
        """Gets the hashed uuid from the incoming record."""
        return record['hashedUuid']

    def _get_record_from_line(self, deserialized_line: dict) -> dict:
        """Extracts the record from the deserialized line."""
        return deserialized_line['object']

    def _process_record(self, record: dict) -> None:
        """Processes a single record.

        This method should take a single record, update an existing instance,
        or create a new one, and return None.
        """
        serializer = self.serializer_class(data=record)
        if serializer.is_valid():
            primary_key = UUID(serializer.validated_data.pop('id'))
            queryset = PostcodeData.objects.filter(pk=primary_key)
            instance, created = queryset.update_or_create(
                pk=primary_key,
                defaults=serializer.validated_data,
            )
            if created:
                self.created_ids.append(str(instance.id))
            else:
                self.updated_ids.append(str(instance.id))
        else:
            self.errors.append({
                'record': record,
                'errors': serializer.errors,
            })

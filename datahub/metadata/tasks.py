import logging

from rest_framework import serializers

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import BaseObjectIdentificationTask, BaseObjectIngestionTask
from datahub.metadata.constants import POSTCODE_DATA_PREFIX
from datahub.metadata.models import PostcodeData
from datahub.metadata.serializers import PostcodeDataSerializer


logger = logging.getLogger(__name__)


def postcode_data_identification_task() -> None:
    logger.info('Postcode data identification task started...')
    identification_task = PostcodeDataIdentificationTask(prefix=POSTCODE_DATA_PREFIX)
    identification_task.identify_new_objects(postcode_data_ingestion_task)
    logger.info('Postcode data identification task finished.')


class PostcodeDataIdentificationTask(BaseObjectIdentificationTask):
    """Class to identify new postcode data objects and determine if they should be ingested."""


def postcode_data_ingestion_task(object_key: str) -> None:
    logger.info('Postcode data ingestion task started...')
    ingestion_task = PostcodeDataIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=POSTCODE_DATA_PREFIX),
        serializer_class=PostcodeDataSerializer,
    )
    ingestion_task.ingest_object()
    logger.info('Postcode data ingestion task finished.')


class PostcodeDataIngestionTask(BaseObjectIngestionTask):
    """Class to ingest a postcode object from S3."""

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
                'id', flat=True))

        postcode_data_id = record.get('id')
        if postcode_data_id in self.existing_ids:
            logger.info(f'Record already exists for postcode_data_id: {postcode_data_id}')
            return False

        return True

    def _process_record(self, record: dict) -> None:
        """Processes a single record.

        This method should take a single record, update an existing instance,
        or create a new one, and return None.
        """
        serializer = self.serializer_class(data=record)
        if serializer.is_valid():
            primary_key = serializer.validated_data.pop('id')
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

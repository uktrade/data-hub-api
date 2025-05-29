import itertools
import json
import logging

import smart_open
from django.db import transaction

from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import BaseObjectIdentificationTask, BaseObjectIngestionTask
from datahub.metadata.constants import POSTCODE_DATA_PREFIX
from datahub.metadata.models import PostcodeData

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


def postcode_data_identification_task() -> None:
    logger.info('Postcode data identification task started...')
    identification_task = PostcodeDataIdentificationTask(
        prefix=POSTCODE_DATA_PREFIX,
        job_timeout=HALF_DAY_IN_SECONDS,
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
        super().__init__(object_key, s3_processor)
        self._existing_ids = set(PostcodeData.objects.values_list('id', flat=True))
        self._fields_to_update = PostcodeDataIngestionTask._fields_to_update()
        self.created_count = 0
        self.updated_count = 0
        self.deleted_count = 0
        self.batch_create_count = 0
        self.batch_update_count = 0
        self._batch_create = []
        self._batch_update = []
        self._to_delete = []
        self._all_file_ids = set()

    def ingest_object(self) -> None:
        """Process all records in batches from the specified object.."""
        try:
            with smart_open.open(
                f's3://{self.s3_processor.bucket}/{self.object_key}',
                transport_params={'client': self.s3_processor.s3_client},
            ) as s3_object:
                for line in itertools.islice(s3_object, 5000):
                    jsn = json.loads(line)
                    object = PostcodeData(**jsn)

                    if not object.id:
                        continue

                    self._all_file_ids.add(object.id)

                    if object.id in self._existing_ids:
                        self._batch_update.append(object)
                    else:
                        self._batch_create.append(object)

                    # Process batches when they reach batch size
                    if len(self._batch_create) >= BATCH_SIZE:
                        self._process_create_batch()
                    if len(self._batch_update) >= BATCH_SIZE:
                        self._process_update_batch()

                # Process any remaining items in the batch
                if self._batch_create:
                    self._process_create_batch()
                if self._batch_update:
                    self._process_update_batch()

                # Handle deletions after processing all records
                if self._all_file_ids:
                    self._process_deletions()

        except Exception as e:
            logger.error(f'An error occurred trying to process {self.object_key}: {e}')
            raise e

        self._create_ingested_object_instance()
        self._log_ingestion_metrics()

    def _fields_to_update():
        fields = [field.name for field in PostcodeData._meta.get_fields()]
        fields.remove('id')
        return fields

    def _process_create_batch(self) -> None:
        """Process a batch of records to create."""
        if not self._batch_create:
            return

        self.batch_create_count += 1
        logger.info(f'Creating postcode batch {self.batch_create_count}...')

        batch_created_count = len(self._batch_create)

        try:
            with transaction.atomic():
                PostcodeData.objects.bulk_create(self._batch_create, batch_size=BATCH_SIZE)
                logger.info(f'Finished creating postcode batch {self.batch_create_count}')
        except Exception as e:
            logger.warning(f'Error creating batch: {e}')
            self.errors.append(
                {
                    'batch_type': 'create',
                    'batch_size': batch_created_count,
                    'error': str(e),
                },
            )
        finally:
            self._batch_create.clear()

    def _process_update_batch(self) -> None:
        """Process a batch of records to update."""
        if not self._batch_update:
            return

        self.batch_update_count += 1
        logger.info(f'Updating postcode batch {self.batch_update_count}...')

        batch_updated_count = len(self._batch_update)

        try:
            with transaction.atomic():
                PostcodeData.objects.bulk_update(
                    self._batch_update,
                    self._fields_to_update,
                    batch_size=BATCH_SIZE,
                )
                logger.info(f'Finished updating postcode batch {self.batch_update_count}')
                self.updated_count += batch_updated_count
        except Exception as e:
            logger.warning(f'Error updating batch: {e}')
            self.errors.append(
                {
                    'batch_type': 'update',
                    'batch_size': batch_updated_count,
                    'error': str(e),
                },
            )
        finally:
            self._batch_update.clear()

    def _process_deletions(self) -> None:
        """Process deletions in batches."""
        to_delete = self._existing_ids - self._all_file_ids

        if not to_delete:
            logger.info('No postcode records to delete')
            return

        self.batch_update_count += 1
        logger.info(f'Deleting postcode batch {self.batch_update_count}...')

        to_delete_list = list(to_delete)

        for i in range(0, len(to_delete_list), BATCH_SIZE):
            batch = to_delete_list[i : i + BATCH_SIZE]
            try:
                with transaction.atomic():
                    batch_deleted_count, _ = PostcodeData.objects.filter(id__in=batch).delete()
                    logger.info(f'Finished deleting postcode batch {self.batch_update_count}')
                    self.deleted_count += batch_deleted_count
            except Exception as e:
                logger.error(f'Error deleting batch: {e}')
                self.errors.append(
                    {
                        'batch_type': 'delete',
                        'batch_size': len(batch),
                        'error': str(e),
                    },
                )

    def _log_ingestion_metrics(self):
        """Log various metrics after a successful ingestion."""
        logger.info(f'{self.object_key} ingested')
        logger.info(f'{self.created_count} postcode records created')
        logger.info(f'{self.updated_count} postcode records updated')
        logger.info(f'{self.deleted_count} postcode records deleted')

        if self.errors:
            logger.error(
                f'{len(self.errors)} errors during postcode ingestion task: {self.errors}',
            )
        else:
            logger.info('No errors occurred during postcode ingestion task')

        total_processed = len(self._all_file_ids)
        logger.info(f'Total postcode records processed: {total_processed}')
        logger.info(f'Batch size used during postcode ingestion task: {BATCH_SIZE}')

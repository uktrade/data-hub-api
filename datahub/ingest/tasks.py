import json
import logging

import smart_open
from dateutil import parser
from django.conf import settings
from redis import Redis
from rq import Queue, Worker
from rq.job import Job

from datahub.core.queues.constants import THREE_MINUTES_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.models import IngestedObject

logger = logging.getLogger(__name__)


class QueueChecker:
    """Checks the Redis Queue for specific ingestion task."""

    def __init__(self, queue_name: str) -> None:
        self.redis = Redis.from_url(settings.REDIS_BASE_URL)
        self.queue = Queue(queue_name, connection=self.redis)

    def match_job(self, job: Job, ingestion_task_function: callable, object_key: str) -> bool:
        """Determines if the job matches the ingestion task name and object key."""
        function_name = f'{ingestion_task_function.__module__}.{ingestion_task_function.__name__}'
        return job.func_name == function_name and job.kwargs.get('object_key') == object_key

    def is_job_queued(self, ingestion_task_function: callable, object_key: str) -> bool:
        """Check if a job is queued."""
        return any(
            self.match_job(job, ingestion_task_function, object_key) for job in self.queue.jobs
        )

    def is_job_running(self, ingestion_task_function: callable, object_key: str) -> bool:
        """Check if a job is running."""
        for worker in Worker.all(queue=self.queue):
            job = worker.get_current_job()
            if job and self.match_job(job, ingestion_task_function, object_key):
                return True
        return False


class BaseObjectIdentificationTask:
    """Base class to identify new objects in S3 and determine if they should be ingested.

    An example of how this class should be used:
    ```
    def base_identification_task() -> None:
        '''Function to be scheduled and called by an RQ worker to identify objects to ingest.'''
        logger.info('Base identification task started...')
        identification_task = BaseObjectIdentificationTask(prefix='prefix/')
        identification_task.identify_new_objects(base_ingestion_task)
        logger.info('Base identification task finished.')
    ```
    """

    def __init__(self, prefix: str, job_timeout=THREE_MINUTES_IN_SECONDS):
        self.long_queue_checker: QueueChecker = QueueChecker(queue_name='long-running')
        self.s3_processor: S3ObjectProcessor = S3ObjectProcessor(prefix=prefix)
        self.job_timeout = job_timeout

    def identify_new_objects(self, ingestion_task_function: callable) -> None:
        """Entry point method to identify new objects and, if valid, schedule their ingestion."""
        latest_object_key = self.s3_processor.get_most_recent_object_key()

        if not latest_object_key:
            logger.info('No objects found')
            return

        if self.long_queue_checker.is_job_queued(
            ingestion_task_function,
            latest_object_key,
        ):
            logger.info(f'{latest_object_key} has already been queued for ingestion')
            return

        if self.long_queue_checker.is_job_running(
            ingestion_task_function,
            latest_object_key,
        ):
            logger.info(f'{latest_object_key} is currently being ingested')
            return

        if self.s3_processor.has_object_been_ingested(latest_object_key):
            logger.info(f'{latest_object_key} has already been ingested')
            return

        job_scheduler(
            function=ingestion_task_function,
            function_kwargs={
                'object_key': latest_object_key,
            },
            job_timeout=self.job_timeout,
            queue_name=self.long_queue_checker.queue.name,
            description=f'Ingest {latest_object_key}',
        )
        logger.info(f'Scheduled ingestion of {latest_object_key}')


def base_ingestion_task(
    object_key: str,
    s3_processor: S3ObjectProcessor,
) -> None:
    """Function to be scheduled by the BaseObjectIdentificationTask.identify_new_objects method.

    Once executed by an RQ worker, it will ingest the specified object.

    This function serves as an example and is only used in tests of the base classes.
    It is not, and should not be, scheduled for execution in `cron-scheduler.py`.
    """
    logger.info('Base ingestion task started...')
    ingestion_task = BaseObjectIngestionTask(
        object_key=object_key,
        s3_processor=s3_processor,
    )
    ingestion_task.ingest_object()
    logger.info('Base ingestion task finished.')


class BaseObjectIngestionTask:
    """Base class to ingest a specified object from S3."""

    def __init__(
        self,
        object_key: str,
        s3_processor: S3ObjectProcessor,
    ) -> None:
        self.object_key = object_key
        self.s3_processor = s3_processor
        self.last_ingestion_datetime = self.s3_processor.get_last_ingestion_datetime()
        self.skipped_counter = 0
        self.created_ids = []
        self.updated_ids = []
        self.errors = []

    def ingest_object(self) -> None:
        """Process all records in the object key specified when the class instance was created."""
        try:
            with smart_open.open(
                f's3://{self.s3_processor.bucket}/{self.object_key}',
                transport_params={'client': self.s3_processor.s3_client},
            ) as s3_object:
                for line in s3_object:
                    deserialized_line = json.loads(line)
                    record = self._get_record_from_line(deserialized_line)
                    if self._should_process_record(record):
                        self._process_record(record)
                    else:
                        self.skipped_counter += 1
        except Exception as e:
            logger.error(f'An error occurred trying to process {self.object_key}: {e}')
            raise e
        self._create_ingested_object_instance()
        self._log_ingestion_metrics()

    def _get_record_from_line(self, deserialized_line: dict) -> dict:
        """Extracts the record from the deserialized line.

        This method should be overridden if the record is nested.
        """
        return deserialized_line

    def _should_process_record(self, record: dict) -> bool:
        """Determine if a record should be processed.

        This method uses the incoming record's last modified date to check
        whether the record should be processed. If the incoming data has a
        similar field, please override the `_get_modified_datetime_str` method to
        specify which field should be used.

        If the record has no modified (or similar) field, please override this
        method to set the desired rules to determine if it's processed or not.
        """
        if self.last_ingestion_datetime is None:
            return True
        try:
            modified_datetime_str = self._get_modified_datetime_str(record)
            modified_datetime = parser.parse(modified_datetime_str)
        except ValueError as e:
            logger.error(
                f'An error occurred determining the last modified datetime: {e}',
            )
            # If unable to parse datetime string, assume record should be processed.
            return True
        return modified_datetime.timestamp() >= self.last_ingestion_datetime.timestamp()

    def _get_modified_datetime_str(self, record: dict) -> str:
        """Gets the last modified datetime string from the incoming record."""
        return record['modified']

    def _process_record(self, record: dict) -> None:
        """Processes a single record.

        This method should take a single record, update an existing instance, or create a new one,
        and return None.

        Depending on preference, you can use a DRF serializer or dictionary of mappings.
        Similarly, you can append information to the created, updated, and error lists for logging.

        See below for an example using a DRF serializer and logging metrics:
        ```
        serializer = SerializerClass(data=record)
        if serializer.is_valid():
            # pop the `id` field from validated data so that it does not attempt to update it
            primary_key = UUID(serializer.validated_data.pop('id'))
            queryset = ModelClass.objects.filter(pk=primary_key)
            instance, created = queryset.update_or_create(
                pk=primary_key,
                defaults=serializer.validated_data,
            )
            if created:
                self.created_ids.append(str(instance.id))
            else:
                self.updated_ids.append(str(instance.id))
        else:
            self.errors.append(
                {
                    'record': record,
                    'errors': serializer.errors,
                }
            )
        ```
        """
        raise NotImplementedError(
            'Please override the _process_record method and tailor to your use case.',
        )

    def _create_ingested_object_instance(self):
        """Record a successful ingestion by creating an IngestedObject instance."""
        last_modified = self.s3_processor.get_object_last_modified_datetime(self.object_key)
        IngestedObject.objects.create(object_key=self.object_key, object_created=last_modified)
        logger.info(f'IngestObject instance created for {self.object_key}.')

    def _log_ingestion_metrics(self):
        """Log various metrics after a successful ingestion.

        Metrics include:
        - Number of and list of instance ids that have been created
        - Number of and list of instance ids that have been updated
        - List of errors that have been raised from individual records
        - Number of records skipped due to the _should_process_record method returning False
        """
        logger.info(f'{self.object_key} ingested.')
        if self.created_ids:
            logger.info(
                f'{len(self.created_ids)} records created: {self.created_ids}',
            )
        if self.updated_ids:
            logger.info(
                f'{len(self.updated_ids)} records updated: {self.updated_ids}',
            )
        if self.errors:
            logger.warning(f'{len(self.errors)} records failed validation: {self.errors}')
        logger.info(
            f'{self.skipped_counter} records skipped.',
        )

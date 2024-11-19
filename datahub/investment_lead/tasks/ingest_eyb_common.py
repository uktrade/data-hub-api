import json
import logging

from datetime import datetime

import environ

from django.conf import settings
from django.db.models import Q
from redis import Redis
from rq import Queue, Worker
from smart_open import open

from datahub.company_activity.models import IngestedFile
from datahub.company_activity.tasks.ingest_company_activity import CompanyActivityIngestionTask
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.investment_lead.models import EYBLead


logger = logging.getLogger(__name__)
env = environ.Env()
REGION = env('AWS_DEFAULT_REGION', default='eu-west-2')
BUCKET = f"data-flow-bucket-{env('ENVIRONMENT', default='')}"
PREFIX = 'data-flow/exports/'
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class BaseEYBFileIngestionTask(CompanyActivityIngestionTask):
    """Task to check for a new EYB file and trigger a long running job to ingest the data."""

    def _has_file_been_queued(self, matching_function, file):
        """Check if there is already an RQ job queued or running to ingest the given file"""
        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        for job in rq_queue.jobs:
            if matching_function(job, file):
                return True
        for worker in Worker.all(queue=rq_queue):
            job = worker.get_current_job()
            if job is not None and matching_function(job, file):
                return True
        return False

    def ingest(self, prefix, matching_function, ingestion_function):
        """
        Gets the most recent file in the data-flow S3 bucket for each
        data source (prefix) and enqueues a job to process each file
        that hasn't already been ingested
        """
        latest_file = self._get_most_recent_obj(BUCKET, prefix)
        if not latest_file:
            logger.info(f'No new files found in {prefix}')
            return

        if self._has_file_been_queued(matching_function, latest_file):
            logger.info(f'{latest_file} has already been queued for ingestion')
            return

        if self._has_file_been_ingested(latest_file):
            logger.info(f'{latest_file} has already been ingested')
            return

        job_scheduler(
            function=ingestion_function,
            function_kwargs={'bucket': BUCKET, 'file': latest_file},
            queue_name='long-running',
            description='Ingest EYB data',
        )
        logger.info(f'Scheduled ingestion of {latest_file}')


class BaseEYBDataIngestionTask:
    """Long running job to read the file contents and ingest the records."""

    def __init__(self, serializer_class, prefix):
        self._last_ingestion_datetime = self._get_last_ingestion_datetime(prefix)
        self.serializer_class = serializer_class
        self.created_hashed_uuids = []
        self.updated_hashed_uuids = []
        self.errors = []

    def ingest(self, bucket, file):
        path = f's3://{bucket}/{file}'
        try:
            with open(path) as s3_file:
                for line in s3_file:
                    jsn = json.loads(line)
                    if self._record_has_no_changes(jsn):
                        continue
                    self.json_to_model(jsn)
        except Exception as e:
            raise e
        IngestedFile.objects.create(filepath=file)
        if self.created_hashed_uuids:
            logger.info(
                f'{len(self.created_hashed_uuids)} records created: {self.created_hashed_uuids}',
            )
        if self.updated_hashed_uuids:
            logger.info(
                f'{len(self.updated_hashed_uuids)} records updated: {self.updated_hashed_uuids}',
            )
        if self.errors:
            logger.warning(f'{len(self.errors)} records failed validation: {self.errors}')

    def _get_last_ingestion_datetime(self, prefix):
        try:
            return IngestedFile.objects.filter(
                filepath__icontains=prefix,
            ).latest('created_on').created_on
        except IngestedFile.DoesNotExist:
            return None

    def _record_has_no_changes(self, record):
        if self._last_ingestion_datetime is None:
            return False
        else:
            date_str = record['object']['modified']
            try:
                date = datetime.strptime(date_str, DATE_FORMAT)
            except ValueError:
                date = datetime.fromisoformat(date_str)
            return date.timestamp() < self._last_ingestion_datetime.timestamp()

    def _get_hashed_uuid(self, obj):
        """
        Method to get the hashed uuid from the incoming json object.
        """
        raise NotImplementedError

    def json_to_model(self, jsn):
        obj = jsn['object']
        serializer = self.serializer_class(data=obj)
        hashed_uuid = self._get_hashed_uuid(obj)
        if serializer.is_valid():
            queryset = EYBLead.objects.filter(
                Q(user_hashed_uuid=hashed_uuid)
                | Q(triage_hashed_uuid=hashed_uuid)
                | Q(marketing_hashed_uuid=hashed_uuid),
            )
            instance, created = queryset.update_or_create(defaults=serializer.validated_data)
            if created:
                self.created_hashed_uuids.append(hashed_uuid)
            else:
                self.updated_hashed_uuids.append(hashed_uuid)
        else:
            self.errors.append({
                'index': hashed_uuid,
                'errors': serializer.errors,
            })

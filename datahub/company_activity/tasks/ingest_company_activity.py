import logging

import boto3
import environ

from django.conf import settings

from redis import Redis
from rq import Queue, Worker

from datahub.company_activity.models import IngestedFile
from datahub.company_activity.tasks import ingest_great_data
from datahub.core.queues.job_scheduler import job_scheduler

logger = logging.getLogger(__name__)
env = environ.Env()
REGION = env('AWS_DEFAULT_REGION', default='eu-west-2')
BUCKET = f"data-flow-bucket-{env('ENVIRONMENT', default='')}"
PREFIX = 'data-flow/exports/'
GREAT_PREFIX = f'{PREFIX}GreatGovUKFormsPipeline/'


def ingest_activity_data():
    logger.info('Checking for new Company Activity data files')
    task = CompanyActivityIngestionTask()
    task.ingest()


class CompanyActivityIngestionTask:
    def _list_objects(self, bucket_name, prefix):
        """Returns a list all objects with specified prefix."""
        s3_client = boto3.client('s3', REGION)
        response = s3_client.list_objects(
            Bucket=bucket_name,
            Prefix=prefix,
        )
        return [object.get('Key', None) for object in response.get('Contents', {})]

    def _get_most_recent_obj(self, bucket_name, prefix):
        """Returns the most recent file object in the given bucket/prefix"""
        files = self._list_objects(bucket_name, prefix)
        if files:
            files.sort(reverse=True)
            return files[0]

    def _has_file_been_ingested(self, file):
        """Check if the given file has already been successfully ingested"""
        previously_ingested = IngestedFile.objects.filter(filepath=file)
        return previously_ingested.exists()

    def _job_matches(self, job, file):
        func_name = 'datahub.company_activity.tasks.ingest_great_data.ingest_great_data'
        return job.kwargs.get('file') == file and job.func_name == func_name

    def _has_file_been_queued(self, file):
        """Check if there is already an RQ job queued or running to ingest the given file"""
        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        for job in rq_queue.jobs:
            if self._job_matches(job, file):
                return True
        for worker in Worker.all(queue=rq_queue):
            job = worker.get_current_job()
            if job is not None and self._job_matches(job, file):
                return True
        return False

    def ingest(self):
        """
        Gets the most recent file in the data-flow S3 bucket for each
        data source (prefix) and enqueues a job to process each file
        that hasn't already been ingested
        """
        latest_file = self._get_most_recent_obj(BUCKET, GREAT_PREFIX)
        if not latest_file:
            logger.info('No files found')
            return

        if self._has_file_been_queued(latest_file):
            logger.info(f'{latest_file} has already been queued for ingestion')
            return

        if self._has_file_been_ingested(latest_file):
            logger.info(f'{latest_file} has already been ingested')
            return

        job_scheduler(
            function=ingest_great_data,
            function_kwargs={'bucket': BUCKET, 'file': latest_file},
            queue_name='long-running',
            description='Ingest Great data file',
        )
        logger.info(f'Scheduled ingestion of {latest_file}')

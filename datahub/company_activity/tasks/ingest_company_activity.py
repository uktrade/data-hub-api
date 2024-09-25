import boto3
import environ

from django.conf import settings

from redis import Redis
from rq import Queue

from datahub.company_activity.models import IngestedFile

env = environ.Env()
REGION = env('AWS_DEFAULT_REGION')
BUCKET = 'data-flow-bucket' + env('environment', default='')
PREFIX = 'data-flow/exports/'
GREAT_PREFIX = PREFIX + 'GreatGovUKFormsPipeline/'


class CompanyActivityIngestionTask:
    def __init__(self):
        self.s3_client = boto3.client('s3', REGION)

    def _list_objects(self, bucket_name, prefix):
        """Returns a list all objects with specified prefix."""
        response = self.s3_client.list_objects(
            Bucket=bucket_name,
            Prefix=prefix,
        )
        return [object['Key'] for object in response['Contents']]

    def _get_most_recent_obj(self, bucket_name, prefix):
        """Returns the most recent file object in the given bucket/prefix"""
        files = self._list_objects(bucket_name, prefix)
        files.sort(reverse=True)
        return files[0]

    def _has_file_been_ingested(self, file):
        previously_ingested = IngestedFile.objects.filter(filepath=file)
        return previously_ingested.count() > 0

    def ingest_activity_data(self):
        """
        Gets the most recent file in the data-flow S3 bucekt for each
        data source (prefix) and enqueues a job to process each file
        that hasn't already been ingested
        """
        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        latest_file = self._get_most_recent_obj(BUCKET, GREAT_PREFIX)
        if not self._has_file_been_ingested(latest_file):
            rq_queue.enqueue(ingest_great_data, latest_file)


def ingest_great_data(file):
    pass

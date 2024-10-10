import json
import logging

from datetime import datetime

import environ

from smart_open import open

from datahub.company_activity.models import IngestedFile
from datahub.company_activity.tasks.ingest_company_activity import CompanyActivityIngestionTask
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import CreateEYBLeadTriageSerializer


logger = logging.getLogger(__name__)
env = environ.Env()
REGION = env('AWS_DEFAULT_REGION', default='eu-west-2')
BUCKET = f"data-flow-bucket-{env('ENVIRONMENT', default='')}"
PREFIX = 'data-flow/exports/'
TRIAGE_PREFIX = f'{PREFIX}DirectoryExpandYourBusinessTriageDataPipeline'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


def ingest_eyb_triage_file():
    logger.info('Checking for new EYB triage files')
    task = EYBTriageFileIngestionTask()
    task.ingest()


class EYBTriageFileIngestionTask(CompanyActivityIngestionTask):
    """Task to check for new triage file and trigger long running job."""

    def _job_matches(self, job, file):
        func_name = 'datahub.investment_lead.tasks.ingest_eyb_triage.ingest_eyb_triage_data'
        return job.kwargs.get('file') == file and job.func_name == func_name

    def ingest(self):
        """
        Gets the most recent file in the data-flow S3 bucket for each
        data source (prefix) and enqueues a job to process each file
        that hasn't already been ingested
        """
        latest_file = self._get_most_recent_obj(BUCKET, TRIAGE_PREFIX)
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
            function=ingest_eyb_triage_data,
            function_kwargs={'bucket': BUCKET, 'file': latest_file},
            queue_name='long-running',
            description='Ingest EYB triage data.',
        )
        logger.info(f'Scheduled ingestion of {latest_file}')


def ingest_eyb_triage_data(bucket, file):
    logger.info(f'Ingesting file: {file} started')
    task = EYBTriageDataIngestionTask()
    task.ingest(bucket, file)
    logger.info(f'Ingesting file: {file} finished')


class EYBTriageDataIngestionTask:
    """Long running job to read the file contents and create model instances from records."""

    def __init__(self):
        self._last_ingestion_datetime = self._get_last_ingestion_datetime()

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
        logger.info(f'{EYBLead.objects.count()} leads ingested!')

    def _get_last_ingestion_datetime(self):
        try:
            return IngestedFile.objects.latest('created_on').created_on.timestamp()
        except IngestedFile.DoesNotExist:
            return None

    def _record_has_no_changes(self, record):
        if self._last_ingestion_datetime is None:
            return False
        else:
            date = datetime.strptime(record['object']['modified'], DATE_FORMAT).timestamp()
            return date < self._last_ingestion_datetime

    def json_to_model(self, jsn):
        obj = jsn['object']
        logger.info(f'{obj=}')
        serializer = CreateEYBLeadTriageSerializer(data=obj)
        if serializer.is_valid():
            logger.info(f'{serializer.data=}')
            # TODO: potential race condition where user and triage jobs run simultaneously?
            EYBLead.objects.update_or_create(
                user_hashed_uuid=obj['hashedUuid'],
                defaults=serializer.validated_data,
            )
        logger.info(f'{serializer.errors=}')

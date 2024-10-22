import logging

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.investment_lead.serializers import CreateEYBLeadTriageSerializer
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BaseEYBDataIngestionTask,
    BaseEYBFileIngestionTask,
    PREFIX,
)
from datahub.investment_lead.tasks.ingest_eyb_user import ingest_eyb_user_file


logger = logging.getLogger(__name__)
TRIAGE_PREFIX = f'{PREFIX}DirectoryExpandYourBusinessTriageDataPipeline/'


def ingest_eyb_triage_file():
    logger.info('Checking for new EYB triage files')
    task = EYBTriageFileIngestionTask()
    task.ingest()


class EYBTriageFileIngestionTask(BaseEYBFileIngestionTask):
    """Task to check for new triage file and trigger long running job."""

    def _job_matches(self, job, file):
        func_name = 'datahub.investment_lead.tasks.ingest_eyb_triage.ingest_eyb_triage_data'
        return job.kwargs.get('file') == file and job.func_name == func_name

    def ingest(self):
        super().ingest(TRIAGE_PREFIX, self._job_matches, ingest_eyb_triage_data)


def ingest_eyb_triage_data(bucket, file):
    """Ingests triage data from the file passed in.

    Schedules the user data ingetion job after the triage ingestion job to prevent
    the risk of duplicate instances of the same lead being created.
    Triage data and user data are combined using a UUID to create/update a single EYB Lead.
    """
    logger.info(f'Ingesting file: {file} started')
    task = EYBTriageDataIngestionTask(
        serializer_class=CreateEYBLeadTriageSerializer,
        prefix=TRIAGE_PREFIX,
    )
    task.ingest(bucket, file)
    logger.info(f'Ingesting file: {file} finished')

    job_scheduler(
        function=ingest_eyb_user_file,
        description='Check S3 for new EYB user data files and ingest',
    )
    logger.info('Ingest EYB triage data job has scheduled EYB user file job')


class EYBTriageDataIngestionTask(BaseEYBDataIngestionTask):
    """Long running job to read the triage file contents and ingest the records."""

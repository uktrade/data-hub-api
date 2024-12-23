import logging

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.investment_lead.serializers import CreateEYBLeadUserSerializer
from datahub.investment_lead.services import link_leads_to_companies
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BaseEYBDataIngestionTask,
    BaseEYBFileIngestionTask,
    PREFIX,
)
from datahub.investment_lead.tasks.ingest_eyb_marketing import (
    ingest_eyb_marketing_file,
)


logger = logging.getLogger(__name__)
USER_PREFIX = f'{PREFIX}DirectoryExpandYourBusinessUserDataPipeline/'


def ingest_eyb_user_file():
    logger.info('Checking for new EYB user files')
    task = EYBUserFileIngestionTask()
    task.ingest()


class EYBUserFileIngestionTask(BaseEYBFileIngestionTask):
    """Task to check for new user file and trigger long running job."""

    def _job_matches(self, job, file):
        func_name = 'datahub.investment_lead.tasks.ingest_eyb_user.ingest_eyb_user_data'
        return job.kwargs.get('file') == file and job.func_name == func_name

    def ingest(self):
        super().ingest(USER_PREFIX, self._job_matches, ingest_eyb_user_data)


def ingest_eyb_user_data(bucket, file):
    logger.info(f'Ingesting file: {file} started')
    task = EYBUserDataIngestionTask(
        serializer_class=CreateEYBLeadUserSerializer,
        prefix=USER_PREFIX,
    )
    task.ingest(bucket, file)
    logger.info(f'Ingesting file: {file} finished')

    link_leads_to_companies()
    logger.info('Linked leads to companies')

    # Chain next job (EYB marketing file) to avoid creating duplicate EYB Leads.
    job_scheduler(
        function=ingest_eyb_marketing_file,
        description='Check S3 for new EYB marketing files and ingest',
    )
    logger.info('Ingest EYB user data job has scheduled EYB marketing file job')


class EYBUserDataIngestionTask(BaseEYBDataIngestionTask):
    """Long running job to read the user file contents and ingest the records."""

    def _get_hashed_uuid(self, obj):
        return obj.get('hashedUuid', None)

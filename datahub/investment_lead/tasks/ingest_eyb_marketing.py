import logging

from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import CreateEYBLeadMarketingSerializer
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BaseEYBDataIngestionTask,
    BaseEYBFileIngestionTask,
    PREFIX,
)


logger = logging.getLogger(__name__)
MARKETING_PREFIX = f'{PREFIX}ExportEYBAnalyticsToDataHubS3/'


def ingest_eyb_marketing_file():
    logger.info('Checking for new EYB marketing files')
    task = EYBMarketingFileIngestionTask()
    task.ingest()


class EYBMarketingFileIngestionTask(BaseEYBFileIngestionTask):
    """Task to check for new marketing file and trigger long running job."""

    def _job_matches(self, job, file):
        func_name = 'datahub.investment_lead.tasks.ingest_eyb_marketing.ingest_eyb_marketing_data'
        return job.kwargs.get('file') == file and job.func_name == func_name

    def ingest(self):
        super().ingest(MARKETING_PREFIX, self._job_matches, ingest_eyb_marketing_data)


def ingest_eyb_marketing_data(bucket, file):
    """Ingests marketing data from the file passed in.

    A chain of tasks is created schedules triage ingestion which in turn schedules the user data
    ingestion which in turn schedules marketing data ingestion.
    This to prevent the risk of duplicate instances of the same lead being created.
    Marketing data and user data are combined using a UUID to create/update a single EYB Lead.
    """
    logger.info(f'Ingesting file: {file} started')
    task = EYBMarketingDataIngestionTask(
        serializer_class=CreateEYBLeadMarketingSerializer,
        prefix=MARKETING_PREFIX,
    )
    task.ingest(bucket, file)
    logger.info(f'Ingesting file: {file} finished')


class EYBMarketingDataIngestionTask(BaseEYBDataIngestionTask):
    """Long running job to read the marketing file contents and ingest the records."""

    def _get_hashed_uuid(self, obj):
        return None if obj is None else obj.get('hashed_uuid', None)

    def _record_has_no_changes(self, record):
        hashed_uuid = self._get_hashed_uuid(record.get('object'))
        if hashed_uuid and EYBLead.objects.filter(marketing_hashed_uuid=hashed_uuid).exists():
            return True
        return False

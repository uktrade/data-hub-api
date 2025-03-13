import logging

from datahub.core.queues.constants import THIRTY_MINUTES_IN_SECONDS
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.constants import DATA_FLOW_EXPORTS_PREFIX
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import CreateEYBLeadMarketingSerializer
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BaseEYBIdentificationTask,
    BaseEYBIngestionTask,
)


MARKETING_PREFIX = f'{DATA_FLOW_EXPORTS_PREFIX}ExportEYBAnalyticsToDataHubS3/'


logger = logging.getLogger(__name__)


def eyb_marketing_identification_task() -> None:
    logger.info('EYB marketing identification task started...')
    identification_task = EYBMarketingIdentificationTask(
        prefix=MARKETING_PREFIX,
        job_timeout=THIRTY_MINUTES_IN_SECONDS,
    )
    identification_task.identify_new_objects(eyb_marketing_ingestion_task)
    logger.info('EYB marketing identification task finished.')


class EYBMarketingIdentificationTask(BaseEYBIdentificationTask):
    """Class to identify new EYB marketing objects and determine if they should be ingested."""


def eyb_marketing_ingestion_task(object_key: str) -> None:
    logger.info('EYB marketing ingestion task started...')
    ingestion_task = EYBMarketingIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=MARKETING_PREFIX),
        serializer_class=CreateEYBLeadMarketingSerializer,
    )
    ingestion_task.ingest_object()
    logger.info('EYB marketing ingestion task finished.')


class EYBMarketingIngestionTask(BaseEYBIngestionTask):
    """Class to ingest a specific EYB marketing object from S3."""

    def _get_hashed_uuid(self, record: dict) -> str:
        """Gets the hashed uuid from the incoming record."""
        return record['hashed_uuid']

    def _get_record_from_line(self, deserialized_line: dict) -> dict:
        """Extracts the record from the deserialized line."""
        return deserialized_line

    def _should_process_record(self, record: dict) -> bool:
        """Determine if a record should be processed."""
        hashed_uuid = self._get_hashed_uuid(record)
        if EYBLead.objects.filter(marketing_hashed_uuid=hashed_uuid).exists():
            return False
        return True

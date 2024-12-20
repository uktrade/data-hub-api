import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from datahub.company_activity.models import StovaEvent
from datahub.company_activity.tasks.constants import STOVA_EVENT_PREFIX
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import BaseObjectIdentificationTask, BaseObjectIngestionTask


logger = logging.getLogger(__name__)
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


def ingest_stova_event_data() -> None:
    """Identifies the most recent file to be ingested and schedules a task to ingest it"""
    logger.info('Stova event identification task started.')
    identification_task = StovaEventIndentificationTask(prefix=STOVA_EVENT_PREFIX)
    identification_task.identify_new_objects(stova_ingestion_task)
    logger.info('Stova event identification task finished.')


def stova_ingestion_task(object_key: str) -> None:
    """Ingest the given key (file) from S3"""
    logger.info(f'Stova event ingestion task started for file {object_key}.')
    ingestion_task = StovaEventIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=STOVA_EVENT_PREFIX),
    )
    ingestion_task.ingest_object()
    logger.info(f'Stova event ingestion task finished for file {object_key}.')


class StovaEventIndentificationTask(BaseObjectIdentificationTask):
    pass


class StovaEventIngestionTask(BaseObjectIngestionTask):

    existing_ids = []

    def _process_record(self, record: dict) -> None:
        """Saves an event from Stova from the S3 bucket into a `StovaEvent`"""
        if not self.existing_ids:
            self.existing_ids = set(StovaEvent.objects.values_list('stova_event_id', flat=True))

        stova_event_id = record.get('id')
        if stova_event_id in self.existing_ids:
            logger.info(f'Record already exists for stova_event_id: {stova_event_id}')
            return

        values = {
            'stova_event_id': stova_event_id,
            'url': record.get('url', ''),
            'city': record.get('city', ''),
            'code': record.get('code', ''),
            'name': record.get('name', ''),
            'state': record.get('state', ''),
            'country': record.get('country', ''),
            'max_reg': record.get('max_reg'),
            'end_date': record.get('end_date'),
            'timezone': record.get('timezone', ''),
            'folder_id': record.get('folder_id'),
            'live_date': record.get('live_date'),
            'close_date': record.get('close_date'),
            'created_by': record.get('created_by'),
            'price_type': record.get('price_type', ''),
            'start_date': record.get('start_date'),
            'description': record.get('description', ''),
            'modified_by': record.get('modified_by'),
            'contact_info': record.get('contact_info', ''),
            'created_date': record.get('created_date'),
            'location_city': record.get('location_city', ''),
            'location_name': record.get('location_name', ''),
            'modified_date': record.get('modified_date'),
            'client_contact': record.get('client_contact'),
            'location_state': record.get('location_state', ''),
            'default_language': record.get('default_language', ''),
            'location_country': record.get('location_country', ''),
            'approval_required': record.get('approval_required'),
            'location_address1': record.get('location_address1', ''),
            'location_address2': record.get('location_address2', ''),
            'location_address3': record.get('location_address3', ''),
            'location_postcode': record.get('location_postcode', ''),
            'standard_currency': record.get('standard_currency', ''),
        }

        try:
            StovaEvent.objects.create(**values)
        except IntegrityError as error:
            logger.error(
                f'Error processing Stova event record, stova_event_id: {stova_event_id}. '
                f'Error: {error}',
            )
        except ValidationError as error:
            logger.error(
                'Got unexpected value for a field when processing Stova event record, '
                f'stova_event_id: {stova_event_id}. '
                f'Error: {error}',
            )

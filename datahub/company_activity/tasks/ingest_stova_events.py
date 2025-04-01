import logging

from django.core.exceptions import ValidationError

from datahub.company_activity.models import StovaEvent
from datahub.company_activity.tasks.constants import STOVA_EVENT_PREFIX
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import BaseObjectIdentificationTask, BaseObjectIngestionTask

logger = logging.getLogger(__name__)
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


def stova_event_identification_task() -> None:
    """Identifies the most recent file to be ingested and schedules a task to ingest it."""
    logger.info('Stova event identification task started.')
    identification_task = StovaEventIdentificationTask(prefix=STOVA_EVENT_PREFIX)
    identification_task.identify_new_objects(stova_event_ingestion_task)
    logger.info('Stova event identification task finished.')


def stova_event_ingestion_task(object_key: str) -> None:
    """Ingest the given key (file) from S3."""
    logger.info(f'Stova event ingestion task started for file {object_key}.')
    ingestion_task = StovaEventIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=STOVA_EVENT_PREFIX),
    )
    ingestion_task.ingest_object()
    logger.info(f'Stova event ingestion task finished for file {object_key}.')


class StovaEventIdentificationTask(BaseObjectIdentificationTask):
    pass


class StovaEventIngestionTask(BaseObjectIngestionTask):
    existing_ids = []

    def _should_process_record(self, record: dict) -> bool:
        """Checks whether the record has already been ingested or not."""
        if not self.existing_ids:
            self.existing_ids = set(StovaEvent.objects.values_list('stova_event_id', flat=True))

        stova_event_id = record.get('id')
        if stova_event_id in self.existing_ids:
            logger.info(f'Record already exists for stova_event_id: {stova_event_id}')
            return False

        return True

    @staticmethod
    def _required_fields() -> list:
        """Returns a list of fields required for to make a StovaEvent a Data Hub Event.
        Any fields listed here but not provided by Stova will be rejected from ingestion.

        :return: Required fields to save a StovaEvent.
        """
        return [
            'id',
            'name',
            'location_address1',
            'location_city',
        ]

    @staticmethod
    def _convert_fields_from_null_to_blank(values: dict) -> dict:
        """Coverts values from the stova record which could be null into empty strings for saving
        as a Data Hub event.

        :param values: A single Stova Event record from an S3 bucket.
        :return: A single Stova Event record with null/None values replaced with empty strings.
        """
        fields_required_as_blank = [
            'location_address2',
            'location_address3',
            'location_state',
            'location_postcode',
            'description',
        ]

        for field in fields_required_as_blank:
            if values[field] is None:
                values[field] = ''

        return values

    def _process_record(self, record: dict) -> None:
        """Saves an event from Stova from the S3 bucket into a `StovaEvent`."""
        stova_event_id = record.get('id')

        required_fields = self._required_fields()
        for field in required_fields:
            if record[field] is None or record[field] == '':
                logger.info(
                    f'Stova Event with id {stova_event_id} does not have required field {field}. '
                    'This stova event will not be processed into Data Hub.',
                )
                return

        cleaned_record = self._convert_fields_from_null_to_blank(record)

        values = {
            'stova_event_id': cleaned_record.get('id'),
            'url': cleaned_record.get('url', ''),
            'city': cleaned_record.get('city', ''),
            'code': cleaned_record.get('code', ''),
            'name': cleaned_record.get('name', ''),
            'state': cleaned_record.get('state', ''),
            'country': cleaned_record.get('country', ''),
            'max_reg': cleaned_record.get('max_reg'),
            'end_date': cleaned_record.get('end_date'),
            'timezone': cleaned_record.get('timezone', ''),
            'folder_id': cleaned_record.get('folder_id'),
            'live_date': cleaned_record.get('live_date'),
            'close_date': cleaned_record.get('close_date'),
            'created_by': cleaned_record.get('created_by', ''),
            'price_type': cleaned_record.get('price_type', ''),
            'start_date': cleaned_record.get('start_date'),
            'description': cleaned_record.get('description', ''),
            'modified_by': cleaned_record.get('modified_by', ''),
            'contact_info': cleaned_record.get('contact_info', ''),
            'created_date': cleaned_record.get('created_date'),
            'location_city': cleaned_record.get('location_city', ''),
            'location_name': cleaned_record.get('location_name', ''),
            'modified_date': cleaned_record.get('modified_date'),
            'client_contact': cleaned_record.get('client_contact', ''),
            'location_state': cleaned_record.get('location_state', ''),
            'default_language': cleaned_record.get('default_language', ''),
            'location_country': cleaned_record.get('location_country', ''),
            'approval_required': cleaned_record.get('approval_required'),
            'location_address1': cleaned_record.get('location_address1', ''),
            'location_address2': cleaned_record.get('location_address2', ''),
            'location_address3': cleaned_record.get('location_address3', ''),
            'location_postcode': cleaned_record.get('location_postcode', ''),
            'standard_currency': cleaned_record.get('standard_currency', ''),
        }

        try:
            stova_event = StovaEvent(**values)
            # Raises Validation errors if there are any with the field/s which errored
            stova_event.full_clean()
            stova_event.save()
        except ValidationError as error:
            logger.error(
                'Got unexpected value for a field when processing Stova event record, '
                f'stova_event_id: {stova_event_id}. '
                f'Error: {error}',
            )

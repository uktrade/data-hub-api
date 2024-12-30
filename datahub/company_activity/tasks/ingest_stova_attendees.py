import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from datahub.company_activity.models import StovaAttendee
from datahub.company_activity.tasks.constants import STOVA_ATTENDEE_PREFIX
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import BaseObjectIdentificationTask, BaseObjectIngestionTask


logger = logging.getLogger(__name__)
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


def ingest_stova_attendee_data() -> None:
    """Identifies the most recent file to be ingested and schedules a task to ingest it"""
    logger.info('Stova attendee identification task started.')
    identification_task = StovaAttendeeIndentificationTask(prefix=STOVA_ATTENDEE_PREFIX)
    identification_task.identify_new_objects(stova_attendee_ingestion_task)
    logger.info('Stova attendee identification task finished.')


def stova_attendee_ingestion_task(object_key: str) -> None:
    """Ingest the given key (file) from S3"""
    logger.info(f'Stova attendee ingestion task started for file {object_key}.')
    ingestion_task = StovaAttendeeIngestionTask(
        object_key=object_key,
        s3_processor=S3ObjectProcessor(prefix=STOVA_ATTENDEE_PREFIX),
    )
    ingestion_task.ingest_object()
    logger.info(f'Stova attendee ingestion task finished for file {object_key}.')


class StovaAttendeeIndentificationTask(BaseObjectIdentificationTask):
    pass


class StovaAttendeeIngestionTask(BaseObjectIngestionTask):

    existing_ids = []

    def _process_record(self, record: dict) -> None:
        """Saves an attendee from Stova from the S3 bucket into a `Stovaattendee`"""
        if not self.existing_ids:
            self.existing_ids = set(
                StovaAttendee.objects.values_list('stova_attendee_id', flat=True)
            )

        stova_attendee_id = record.get('id')
        if stova_attendee_id in self.existing_ids:
            logger.info(f'Record already exists for stova_attendee_id: {stova_attendee_id}')
            return

        values = {
            'stova_attendee_id': stova_attendee_id,
            'stova_event_id': record.get('event_id', ''),
            'created_date': record.get('created_date'),
            'email': record.get('email', ''),
            'first_name': record.get('first_name', ''),
            'last_name': record.get('last_name', ''),
            'company_name': record.get('company_name', ''),
            'category': record.get('category', ''),
            'registration_status': record.get('registration_status', ''),
            'created_by': record.get('created_by', ''),
            'language': record.get('language', ''),
            'modified_date': record.get('modified_date'),
            'virtual_event_attendance': record.get('virtual_event_attendance', ''),
            'last_lobby_login': record.get('last_lobby_login', ''),
            'attendee_questions': record.get('attendee_questions', ''),
            'modified_by': record.get('modified_by', ''),
        }

        try:
            StovaAttendee.objects.create(**values)
        except IntegrityError as error:
            logger.error(
                f'Error processing Stova attendee record, stova_attendee_id: {stova_attendee_id}. '
                f'Error: {error}',
            )
        except ValidationError as error:
            logger.error(
                'Got unexpected value for a field when processing Stova attendee record, '
                f'stova_attendee_id: {stova_attendee_id}. '
                f'Error: {error}',
            )

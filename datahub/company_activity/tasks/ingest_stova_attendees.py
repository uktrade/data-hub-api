import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from datahub.company.models import Company
from datahub.company.models import Contact
from datahub.company_activity.models import StovaAttendee
from datahub.company_activity.models import StovaEvent
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
        """
        Processes a single stova attendee from the S3 Bucket and saves it to the `StovaAttendee`
        model. It also attempts to match the contact and company from the given fields and if no
        match is found it creates them.

        :param record: The deserialize JSON row from the S3 Bucket containing stova attendee
            details.
        :returns: None
        """
        if not self.existing_ids:
            self.existing_ids = set(
                StovaAttendee.objects.values_list('stova_attendee_id', flat=True),
            )

        stova_attendee_id = record.get('id')
        if stova_attendee_id in self.existing_ids:
            logger.info(
                f'Record already exists for stova_attendee_id: {stova_attendee_id}',
            )
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

        event = self.get_event_from_attendee(values)
        if not event:
            return

        # Wrap in transaction as we don't want to create any companies/contacts/attendees if any of
        # the steps fail.
        with transaction.atomic():
            company = self.get_or_create_company(values)
            if not company:
                return

            contact = self.get_or_create_contact(values, company)
            if not contact:
                return

            self.create_assignee(values, company, contact, event)

    @staticmethod
    def create_assignee(
        values: dict,
        company: Company,
        contact: Contact,
        event: StovaEvent,
    ) -> None:
        """
        Creates the Stova Assignee only if it matches a Stova Event.

        :param values: A dictionary of cleaned values from an ingested stova attendee record.
        :param company: `Company` object which the assignee belongs to.
        :param contact: A `Contact` found or created from the attendee record.
        :param event: A `StovaEvent` which the attendee was part of.
        :returns: None
        """
        try:
            StovaAttendee.objects.create(
                **values,
                company=company,
                contact=contact,
                ingested_stova_event=event,
            )
        except IntegrityError as error:
            logger.error(
                'Error processing Stova attendee record, stova_attendee_id: '
                f'{values["stova_attendee_id"]}. Error: {error}',
            )
        except ValidationError as error:
            logger.error(
                'Got unexpected value for a field when processing Stova attendee record, '
                f'stova_attendee_id: {values["stova_attendee_id"]}. Error: {error}',
            )

    @staticmethod
    def get_event_from_attendee(values: dict) -> StovaEvent | None:
        event_id = values['stova_event_id']
        attendee_id = values['stova_attendee_id']
        try:
            return StovaEvent.objects.get(stova_event_id=event_id)
        except StovaEvent.DoesNotExist:
            logger.info(
                'The event associated with this attendee does not exist, skipping attendee with '
                f'attendee_id {attendee_id} and event_id {event_id}',
            )
            return

    @staticmethod
    def get_or_create_company(values: dict) -> Company | None:
        """
        Attempts to find an existing `Company` from the attendees company name, if one does not
        exist create a new one.

        :param values: A dictionary of cleaned values from an ingested stova attendee record.
        :returns: An existing `Company` if found or a newly created `Company`.
        """
        company_name = values['company_name']
        company = Company.objects.filter(name=company_name)
        if company.exists():
            return company[0]

        try:
            return Company.objects.create(name=company_name, source=Company.Source.STOVA)
        except IntegrityError as error:
            logger.error(
                'Error creating company from Stova attendee record, stova_attendee_id: '
                f'{values["stova_attendee_id"]}. Error: {error}',
            )
            return

    @staticmethod
    def get_or_create_contact(values: dict, company: Company) -> Contact | None:
        """
        Attempts to find an existing `Contact` from the attendees name, if one does not exist
        create a new one.

        :param values: A dictionary of cleaned values from an ingested stova attendee record.
        :param company: A `Company` object.
        :returns: An existing `Contact` if found or a newly created `Contact`.
        """
        contact = Contact.objects.filter(email=values['email'])
        if contact.exists():
            return contact[0]

        try:
            return Contact.objects.create(
                email=values['email'],
                first_name=values['first_name'],
                last_name=values['last_name'],
                company=company,
                source=Contact.Source.STOVA,
                primary=True,
            )
        except IntegrityError as error:
            logger.error(
                'Error creating contact from Stova attendee record, stova_attendee_id: '
                f'{values["stova_attendee_id"]}. Error: {error}',
            )
            return

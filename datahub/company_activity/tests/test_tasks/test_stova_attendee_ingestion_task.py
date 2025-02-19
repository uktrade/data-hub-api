import logging

from datetime import datetime
from unittest import mock

import pytest

from django.test import override_settings
from moto import mock_aws

from datahub.company.models import Advisor as Adviser, Company, Contact
from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.company_activity.models import StovaAttendee
from datahub.company_activity.tasks.constants import STOVA_ATTENDEE_PREFIX
from datahub.company_activity.tasks.ingest_stova_attendees import (
    stova_attendee_identification_task,
    stova_attendee_ingestion_task,
    StovaAttendeeIngestionTask,
)
from datahub.company_activity.tests.factories import (
    StovaAttendeeFactory,
    StovaEventFactory,
)
from datahub.ingest.models import IngestedObject
from datahub.ingest.utils import (
    compressed_json_faker,
    upload_objects_to_s3,
)
from datahub.interaction.models import Interaction


@pytest.fixture
def test_file():
    filepath = (
        'datahub/company_activity/tests/test_tasks/fixtures/stova/stovaAttendeeFake.jsonl.gz'
    )
    return open(filepath, 'rb')


@pytest.fixture
def test_file_path():
    return f'{STOVA_ATTENDEE_PREFIX}stovaAttendeeFake.jsonl.gz'


@pytest.fixture
def prefix():
    return STOVA_ATTENDEE_PREFIX


@pytest.fixture
def test_base_stova_attendee():
    event_id = 1234
    StovaEventFactory(stova_event_id=event_id)

    return {
        'id': 2367,
        'event_id': event_id,
        'email': 'test@test.com',
        'first_name': 'John',
        'last_name': 'Smith',
        'company_name': 'Test Stova Attendee company',
        'category': 'performance',
        'registration_status': 'blah',
        'created_by': 'Jane',
        'language': 'English',
        'created_date': '2024-10-08 10:46:24.978381+00:00',
        'modified_date': '2024-10-08 10:46:24.978381+00:00',
        'virtual_event_attendance': 'yes',
        'last_lobby_login': '2024-10-08 10:46:24.978381+00:00',
        'attendee_questions': 'What is this event for?',
        'modified_by': 'Jane',
    }


def create_stova_event_records():
    """
    Attendees will only be ingested if their associated StovaEvent exists. This creates some
    initial test events from the event ids in the test fixture for the attendees.
    """
    StovaEventFactory(stova_event_id=3332)
    StovaEventFactory(stova_event_id=3032)
    StovaEventFactory(stova_event_id=8277)
    StovaEventFactory(stova_event_id=3940)


class TestStovaIngestionTasks:

    @pytest.mark.django_db
    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_stova_data_file_ingestion(
        self, caplog, test_file, test_file_path, s3_object_processor,
    ):
        """
        Test that a Aventri/Stova data file is ingested correctly and the ingested file
        is added to the IngestedObject table
        """
        initial_stova_activity_count = StovaAttendee.objects.count()
        initial_ingested_count = IngestedObject.objects.count()

        object_definition = (test_file_path, test_file)
        upload_objects_to_s3(s3_object_processor, [object_definition])

        # Create events for the attendees to be assigned to
        create_stova_event_records()

        with caplog.at_level(logging.INFO):
            stova_attendee_identification_task()
            assert 'Stova attendee identification task started.' in caplog.text
            assert 'Stova attendee identification task finished.' in caplog.text
            assert (
                f'Stova attendee ingestion task started for file {test_file_path}' in caplog.text
            )
            assert (
                f'Stova attendee ingestion task finished for file {test_file_path}' in caplog.text
            )
        assert StovaAttendee.objects.count() == initial_stova_activity_count + 4
        assert IngestedObject.objects.count() == initial_ingested_count + 1

    @pytest.mark.django_db
    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_skip_previously_ingested_records(
        self, test_file_path, test_base_stova_attendee, s3_object_processor,
    ):
        """Test that we skip updating records that have already been ingested"""
        StovaAttendeeFactory(stova_attendee_id=123456789)
        data = test_base_stova_attendee
        data['id'] = 123456789

        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])

        stova_attendee_ingestion_task(test_file_path)
        assert StovaAttendee.objects.filter(stova_attendee_id=123456789).count() == 1

    @pytest.mark.django_db
    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    @pytest.mark.usefixtures('s3_client')
    def test_invalid_file(self, test_file_path):
        """
        Test that an exception is raised when the file is not valid
        """
        with pytest.raises(Exception) as e:
            stova_attendee_ingestion_task(test_file_path)
        exception = e.value.args[0]
        assert 'The specified key does not exist' in exception
        expected = "key: 'data-flow/exports/ExportAventriAttendees/" 'stovaAttendeeFake.jsonl.gz'
        assert expected in exception

    @pytest.mark.django_db
    def test_stova_attendee_fields_are_saved(self, test_base_stova_attendee):
        """
        Test that the ingested stova attendee fields are saved to the StovaAttendee model.
        """
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)
        result = StovaAttendee.objects.get(stova_attendee_id=2367)

        assert result.stova_event_id == data['event_id']

        data.pop('id')
        data.pop('event_id')
        for field, file_value in data.items():
            model_value = getattr(result, field)

            if type(model_value) is datetime:
                assert str(model_value) == file_value
                continue

            assert model_value == file_value

    @pytest.mark.django_db
    def test_stova_attendee_fields_with_duplicate_attendee_ids_in_db(
        self, test_file_path, test_base_stova_attendee, s3_object_processor, caplog,
    ):
        existing_stova_attendee = StovaAttendeeFactory(stova_attendee_id=123456789)
        data = test_base_stova_attendee
        data['id'] = existing_stova_attendee.stova_attendee_id

        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])

        ingestion_task = StovaAttendeeIngestionTask(test_file_path, s3_object_processor)
        with caplog.at_level(logging.INFO):
            ingestion_task.ingest_object()
            assert ingestion_task._should_process_record(data) is False
            assert (
                'Record already exists for stova_attendee_id: '
                f'{existing_stova_attendee.stova_attendee_id}'
            ) in caplog.text

    @pytest.mark.django_db
    def test_stova_attendee_fields_with_duplicate_attendee_ids_in_json(
        self, caplog, test_base_stova_attendee,
    ):
        """
        Test records which have duplicate IDs in their JSON do not raise errors and are handled.
        """
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)

        data = test_base_stova_attendee
        data['id'] = 999999
        task._process_record(data)
        with caplog.at_level(logging.ERROR):
            task._process_record(data)
            assert (
                f'Error processing Stova attendee record, stova_attendee_id: {999999}'
            ) in caplog.text

    @pytest.mark.django_db
    def test_stova_attendee_ingestion_handles_unexpected_fields(
        self, caplog, test_base_stova_attendee,
    ):
        """
        Test that if they rows from stova contain data in an unexpected data type these are handled
        and logged.
        """
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)

        data = test_base_stova_attendee
        stova_attendee_id = data.get('id')

        data['created_date'] = 'Error as not date'

        with caplog.at_level(logging.ERROR):
            task._process_record(data)
            assert (
                'Got unexpected value for a field when processing Stova attendee record, '
                f'stova_attendee_id: {stova_attendee_id}'
            ) in caplog.text

    @pytest.mark.django_db
    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_stova_attendee_ingestion_assigns_attendee_to_event(
        self,
        test_file_path,
        test_base_stova_attendee,
        s3_object_processor,
    ):
        data = test_base_stova_attendee
        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])
        stova_attendee_ingestion_task(test_file_path)

        attendee = StovaAttendee.objects.get(stova_attendee_id=data['id'])
        assert attendee.stova_event_id == data['event_id']
        assert attendee.ingested_stova_event.stova_event_id == data['event_id']

    @pytest.mark.django_db
    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_stova_attendee_ingestion_uses_existing_company_if_found(
        self,
        test_file_path,
        test_base_stova_attendee,
        s3_object_processor,
    ):
        """
        Tests attendee uses existing company if a match is found. This also tests for the
        case-insensitive matches.
        """
        existing_company = CompanyFactory(name='A COMPANY which already exists')

        data = test_base_stova_attendee
        # Same name with different case
        data['company_name'] = 'a company which Already EXISTS'
        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])
        stova_attendee_ingestion_task(test_file_path)

        attendee = StovaAttendee.objects.get(stova_attendee_id=data['id'])
        assert attendee.company_id == existing_company.id

    @pytest.mark.django_db
    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_stova_attendee_ingestion_uses_existing_contact_if_found(
        self,
        test_file_path,
        test_base_stova_attendee,
        s3_object_processor,
    ):
        """
        Tests attendee uses existing contact if a match is found. This also tests for the
        case-insensitive matches.
        """
        data = test_base_stova_attendee
        company = CompanyFactory(name=data['company_name'])
        existing_contact = ContactFactory(email='existing_contact@dbt.com', company=company)

        # Same email with different case
        data['email'] = 'Existing_CONTACT@dbt.com'
        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])
        stova_attendee_ingestion_task(test_file_path)

        attendee = StovaAttendee.objects.get(stova_attendee_id=data['id'])
        assert attendee.contact_id == existing_contact.id

    @pytest.mark.django_db
    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_attendee_is_not_created_if_company_creation_errors(
        self,
        test_file_path,
        test_base_stova_attendee,
        s3_object_processor,
    ):
        invalid_company_name = None

        data = test_base_stova_attendee
        data['company_name'] = invalid_company_name
        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])
        stova_attendee_ingestion_task(test_file_path)

        assert StovaAttendee.objects.filter(stova_attendee_id=data['id']).exists() is False

    @pytest.mark.django_db()
    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_attendee_and_company_are_not_created_if_contact_creation_errors(
        self,
        test_file_path,
        test_base_stova_attendee,
        s3_object_processor,
    ):
        invalid_contact_email = None

        data = test_base_stova_attendee
        data['email'] = invalid_contact_email
        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])
        stova_attendee_ingestion_task(test_file_path)

        assert StovaAttendee.objects.filter(stova_attendee_id=data['id']).exists() is False
        assert Company.objects.filter(name=data['company_name']).exists() is False

    @pytest.mark.django_db
    @mock_aws
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_stova_attendee_not_created_if_event_does_not_exist(
        self, caplog, test_file, test_file_path, s3_object_processor,
    ):
        """
        A StovaEvent needs to exist before ingesting the Stova Attendee.
        """
        object_definition = (test_file_path, test_file)
        upload_objects_to_s3(s3_object_processor, [object_definition])

        with caplog.at_level(logging.INFO):
            stova_attendee_identification_task()
            # These are from the fixture file.
            assert (
                'The event associated with this attendee does not exist, skipping attendee with '
                'attendee_id 245 and event_id 3332' in caplog.text
            )
            assert (
                'The event associated with this attendee does not exist, skipping attendee with '
                'attendee_id 2947 and event_id 3032' in caplog.text
            )
            assert (
                'The event associated with this attendee does not exist, skipping attendee with '
                'attendee_id 2402 and event_id 8277' in caplog.text
            )

        assert StovaAttendee.objects.all().exists() is False

    @pytest.mark.django_db
    def test_stova_attendee_ingestion_creates_default_adviser(
        self, test_base_stova_attendee, s3_object_processor, test_file_path,
    ):
        """Test a default adviser is created when a default does not already exist."""
        data = test_base_stova_attendee
        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])

        ingestion_task = StovaAttendeeIngestionTask(test_file_path, s3_object_processor)
        assert Adviser.objects.filter(
            email='stova_default@businessandtrade.gov.uk',
            first_name='Stova Default',
            last_name='Adviser',
            is_active=False,
        ).exists() is False

        ingestion_task.ingest_object()

        assert Adviser.objects.filter(
            email='stova_default@businessandtrade.gov.uk',
            first_name='Stova Default',
            last_name='Adviser',
            is_active=False,
        ).exists() is True

    @pytest.mark.django_db
    def test_stova_attendee_ingestion_uses_existing_default_adviser_if_exists(
        self, test_base_stova_attendee, s3_object_processor, test_file_path,
    ):
        """Test the default advisor is reused and not created again for each record."""
        data = test_base_stova_attendee
        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])

        ingestion_task = StovaAttendeeIngestionTask(test_file_path, s3_object_processor)

        Adviser.objects.get_or_create(
            email='stova_default@businessandtrade.gov.uk',
            first_name='Stova Default',
            last_name='Adviser',
            is_active=False,
        )

        assert Adviser.objects.filter(
            email='stova_default@businessandtrade.gov.uk',
            first_name='Stova Default',
            last_name='Adviser',
            is_active=False,
        ).count() == 1

        ingestion_task.ingest_object()

        assert Adviser.objects.filter(
            email='stova_default@businessandtrade.gov.uk',
            first_name='Stova Default',
            last_name='Adviser',
            is_active=False,
        ).count() == 1

    @pytest.mark.django_db
    def test_stova_attendee_ingestion_creates_interaction(
        self, test_base_stova_attendee, s3_object_processor, test_file_path,
    ):
        """
        Test that the Stova Attendee ingestion creates an Interaction from the contact (attendee),
        the event (stova event) and the default adviser.
        """
        data = test_base_stova_attendee
        email = 'attendee_in_interaction@test.com'
        data['email'] = email
        object_definition = (test_file_path, compressed_json_faker([data]))
        upload_objects_to_s3(s3_object_processor, [object_definition])

        ingestion_task = StovaAttendeeIngestionTask(test_file_path, s3_object_processor)
        ingestion_task.ingest_object()

        stova_attendee = StovaAttendee.objects.get(email=email)

        contact = Contact.objects.filter(email=stova_attendee.email).first()
        assert contact is not None

        interaction = Interaction.objects.filter(
            contacts__id=contact.id,
        ).first()
        assert interaction is not None
        assert interaction.company == contact.company
        assert interaction.companies.count() == 1
        assert interaction.companies.first() == contact.company
        assert interaction.kind == Interaction.Kind.SERVICE_DELIVERY
        assert interaction.is_event is True
        assert interaction.theme == Interaction.Theme.OTHER
        assert interaction.was_policy_feedback_provided is False
        assert interaction.were_countries_discussed is False
        assert interaction.dit_participants.first().adviser.email == (
            'stova_default@businessandtrade.gov.uk'
        )

        datahub_event = stova_attendee.ingested_stova_event.datahub_event.first()
        assert interaction.event_id == datahub_event.id
        assert interaction.date.date() == datahub_event.start_date
        assert interaction.service_id == datahub_event.service_id
        assert interaction.subject == f'Attended {datahub_event.name}'

    @pytest.mark.django_db
    def test_stova_attendee_ingestion_handles_interaction_creation_fail(
        self, s3_object_processor, test_file_path, caplog,
    ):
        """Test that errors raised when creating an interaction are logged."""
        data = {'stova_attendee_id': 1234}
        ingestion_task = StovaAttendeeIngestionTask(test_file_path, s3_object_processor)

        # The Event start_date is used in the interaction as date but is nullable in Event but
        # required by Interactions.
        datahub_event = StovaEventFactory().datahub_event.first()
        datahub_event.start_date = None
        datahub_event.save()

        with caplog.at_level(logging.ERROR):
            interaction = ingestion_task.create_interaction_for_event_and_contact(
                data,
                CompanyFactory(),
                ContactFactory(),
                datahub_event,
                AdviserFactory(),
            )
            assert (
                'Error creating interaction from Stova attendee record, stova_attendee_id: 1234'
            ) in caplog.text
            assert interaction is None

    @pytest.mark.django_db
    @mock.patch(
        'datahub.company_activity.tasks.ingest_stova_attendees'
        '.StovaAttendeeIngestionTask.get_event_from_attendee',
    )
    def test_stova_attendee_does_not_create_attendee_when_interaction_fails(
        self, mocked_get_event_from_attendee, test_base_stova_attendee,
    ):
        """Test that no Stova Attendee is created if the interaction fails to create."""
        # Make event invalid for an interaction
        stova_event = StovaEventFactory()
        datahub_event = stova_event.datahub_event.first()
        datahub_event.start_date = None
        datahub_event.save()
        stova_event.refresh_from_db()
        mocked_get_event_from_attendee.return_value = stova_event

        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)

        assert StovaAttendee.objects.count() == 0

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'company_name',
        (
            '',
            None,
        ),
    )
    def test_get_or_create_company__returns_when_company_name_empty(
        self, s3_object_processor, test_file_path, caplog, company_name,
    ):
        """Tests empty company names are logged and no company is created."""
        data = {'stova_attendee_id': 1234, 'company_name': company_name}
        ingestion_task = StovaAttendeeIngestionTask(test_file_path, s3_object_processor)

        with caplog.at_level(logging.INFO):
            company = ingestion_task.get_or_create_company(data)
            assert 'No company name available, skipping attendee 1234' in caplog.text
            assert company is None

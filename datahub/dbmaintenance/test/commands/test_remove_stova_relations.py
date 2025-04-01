from unittest import mock
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.db import DatabaseError
from reversion.models import Version

from datahub.company.models import Company, Contact
from datahub.company.test.factories import (
    CompanyFactory,
    ContactFactory,
)
from datahub.company_activity.models import TempRelationStorage
from datahub.company_activity.tasks.ingest_stova_attendees import (
    StovaAttendeeIngestionTask,
)
from datahub.company_activity.tests.factories import StovaEventFactory
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import CompanyInteractionFactory


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


@pytest.mark.django_db
class TestRemoveStovaRelationsCommand:
    @pytest.mark.parametrize(
        ('simulate'),
        [
            False,
            pytest.param(True, marks=pytest.mark.xfail(strict=True)),
        ],
    )
    def test_interactions_from_stova_are_removed(self, test_base_stova_attendee, simulate, caplog):
        """Test interactions created by Stova Attendees are removed and interactions not created by
        stova are not removed.
        """
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)
        data['id'] = 9876
        task._process_record(data)
        data['id'] = 8907
        data['company_name'] = 'a new company'
        task._process_record(data)
        CompanyInteractionFactory.create_batch(5)

        assert Interaction.objects.count() == 8

        caplog.set_level('INFO')
        call_command('remove_stova_relations', simulate=simulate)

        log_text = caplog.text
        assert 'There were 3 interactions deleted out of 3' in log_text
        assert Interaction.objects.count() == 5

    @pytest.mark.parametrize(
        ('simulate'),
        [
            False,
            pytest.param(True, marks=pytest.mark.xfail(strict=True)),
        ],
    )
    def test_contacts_from_stova_are_removed(self, test_base_stova_attendee, simulate, caplog):
        """Test contacts created by Stova Attendees are removed and contacts not created by stova are
        not removed.
        """
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)
        data['id'] = 9876
        task._process_record(data)
        data['id'] = 8907
        data['company_name'] = 'a new company'
        task._process_record(data)
        ContactFactory.create_batch(5)

        assert Contact.objects.count() == 7

        caplog.set_level('INFO')
        call_command('remove_stova_relations', simulate=simulate)

        log_text = caplog.text
        assert 'There were 2 contacts deleted out of 2' in log_text

        assert Contact.objects.count() == 5

    @pytest.mark.parametrize(
        ('simulate'),
        [
            False,
            pytest.param(True, marks=pytest.mark.xfail(strict=True)),
        ],
    )
    def test_companies_from_stova_are_removed(self, test_base_stova_attendee, simulate, caplog):
        """Test companies created by Stova Attendees are removed and companies not created by stova
        are not removed.
        """
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)
        data['id'] = 9876
        data['company_name'] = 'a new company'
        task._process_record(data)
        CompanyFactory.create_batch(5)

        assert Company.objects.count() == 7

        caplog.set_level('INFO')
        call_command('remove_stova_relations', simulate=simulate)

        log_text = caplog.text
        assert 'There were 2 companies deleted out of 2' in log_text

        assert Company.objects.count() == 5

    def test_reversion_can_recover_deleted_objects(self, test_base_stova_attendee):
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)
        data['id'] = 9876
        data['company_name'] = 'a new company'
        task._process_record(data)

        assert Company.objects.count() == 2
        assert Interaction.objects.count() == 2
        assert Contact.objects.count() == 2

        call_command('remove_stova_relations', simulate=False)

        assert Company.objects.count() == 0
        assert Interaction.objects.count() == 0
        assert Contact.objects.count() == 0

        # Check previous versions exist
        interaction_versions = Version.objects.get_for_model(Interaction)
        assert interaction_versions.count() == 2
        company_versions = Version.objects.get_for_model(Company)
        assert company_versions.count() == 2
        contact_versions = Version.objects.get_for_model(Contact)
        assert contact_versions.count() == 2

        # Check they can be restored
        for version in company_versions:
            version.revision.revert()
        for version in contact_versions:
            version.revision.revert()
        for version in interaction_versions:
            version.revision.revert()

        assert Company.objects.count() == 2
        assert Interaction.objects.count() == 2
        assert Contact.objects.count() == 2

    @patch('datahub.interaction.models.Interaction.delete')
    @patch('datahub.company.models.Contact.delete')
    @patch('datahub.company.models.Company.delete')
    def test_transaction(
        self,
        mocked_interaction_delete,
        mocked_contact_delete,
        mocked_company_delete,
        test_base_stova_attendee,
        caplog,
    ):
        """Tests the transaction is rolled back if there is an issue deleting an object.
        This transaction creates a reversion which should not happen if the delete fails.
        """
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)

        assert Company.objects.count() == 1
        assert Interaction.objects.count() == 1
        assert Contact.objects.count() == 1

        mocked_interaction_delete.side_effect = DatabaseError('Error deleting interaction')
        mocked_contact_delete.side_effect = DatabaseError('Error deleting contact')
        mocked_company_delete.side_effect = DatabaseError('Error deleting company')

        caplog.set_level('INFO')
        call_command('remove_stova_relations', simulate=False)

        log_text = caplog.text
        assert 'Error deleting interaction' in log_text
        assert 'Error deleting contact' in log_text
        assert 'Error deleting company' in log_text

        assert 'There were 0 interactions deleted out of 1' in log_text
        assert 'There were 0 contacts deleted out of 1' in log_text
        assert 'There were 0 companies deleted out of 1' in log_text

        assert Interaction.objects.count() == 1
        assert Company.objects.count() == 1
        assert Contact.objects.count() == 1

        assert Interaction.objects.first().archived_reason is None
        assert Company.objects.first().archived_reason is None
        assert Contact.objects.first().archived_reason is None

        # Check no revisions created as transaction rolled back the changes
        interaction_versions = Version.objects.get_for_model(Interaction)
        assert interaction_versions.count() == 0
        company_versions = Version.objects.get_for_model(Company)
        assert company_versions.count() == 0
        contact_versions = Version.objects.get_for_model(Contact)
        assert contact_versions.count() == 0

    def test_reversion_recover_by_object_id(self, test_base_stova_attendee):
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)

        assert Company.objects.count() == 1
        assert Interaction.objects.count() == 1
        assert Contact.objects.count() == 1

        company_id = Company.objects.first().id
        interaction_id = Interaction.objects.first().id
        contact_id = Contact.objects.first().id

        call_command('remove_stova_relations', simulate=False)

        assert TempRelationStorage.objects.count() == 3

        stored_company_id = TempRelationStorage.objects.get(
            model_name='Company',
            object_id=company_id,
        )
        company_reversion = Version.objects.get_for_model(Company).get(
            object_id=stored_company_id.object_id,
        )
        stored_contact_id = TempRelationStorage.objects.get(
            model_name='Contact',
            object_id=contact_id,
        )
        contact_reversion = Version.objects.get_for_model(Contact).get(
            object_id=stored_contact_id.object_id,
        )
        stored_interaction_id = TempRelationStorage.objects.get(
            model_name='Interaction',
            object_id=interaction_id,
        )
        interaction_reversion = Version.objects.get_for_model(Interaction).get(
            object_id=stored_interaction_id.object_id,
        )
        assert Company.objects.count() == 0
        company_reversion.revision.revert()
        assert Company.objects.count() == 1

        assert Contact.objects.count() == 0
        contact_reversion.revision.revert()
        assert Contact.objects.count() == 1

        assert Interaction.objects.count() == 0
        interaction_reversion.revision.revert()
        assert Interaction.objects.count() == 1

    def test_batch_size(self, test_base_stova_attendee):
        """Test objects are deleted based on their batch_size from the management command."""
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)
        data['id'] = 9876
        task._process_record(data)
        data['id'] = 8907
        data['company_name'] = 'a new company'
        task._process_record(data)
        ContactFactory.create_batch(5)

        assert Contact.objects.count() == 7
        call_command('remove_stova_relations', simulate=False, batch_size=1)
        assert Contact.objects.count() == 6

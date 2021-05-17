from unittest import mock

import pytest

from datahub.bed_api.models import (
    EditAccount,
    EditContact,
    EditEvent, EditEventAttendee,
)
from datahub.bed_api.repositories import (
    AccountRepository,
    ContactRepository,
    EventAttendeeRepository,
    EventRepository,
    SalesforceRepository,
)
from datahub.bed_api.tests.test_utils import (
    create_fail_query_response,
    create_success_query_response,
)


class TestSalesforceRepositoryShould:
    """Unit tests for Base SalesforceRepository"""

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_query_calls_salesforce_query_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test query_more calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = SalesforceRepository(mock_salesforce)
        expected_query = 'test_query'
        expected_included_delete = True

        repository.query(
            expected_query,
            expected_included_delete,
            test=True,
        )

        assert mock_salesforce.query.called
        assert mock_salesforce.query.call_args == mock.call(
            expected_query,
            expected_included_delete,
            test=True,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_query_next_calls_salesforce_query_more_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test query_more calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = SalesforceRepository(mock_salesforce)
        expected_next_records_identifier = 'test_next_id'
        expected_identifier_is_url = True
        expected_included_delete = True

        repository.query_next(
            expected_next_records_identifier,
            expected_identifier_is_url,
            expected_included_delete,
            test=True,
        )

        assert mock_salesforce.query_more.called
        assert mock_salesforce.query_more.call_args == mock.call(
            expected_next_records_identifier,
            expected_identifier_is_url,
            expected_included_delete,
            test=True,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_add_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test add throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.add({'TestData': True})

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_delete_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test delete throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.delete('test_record_id')

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test exists throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.exists('test_record_id')

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test exists throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.get('test_record_id')

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_by_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test get_by throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.get_by('test_field', 'test_record_id')

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_update_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test update throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.update('test_record_id', {'TestData': True})


class TestContactRepositoryShould:
    """Unit tests for ContactRepository"""

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_add_calls_salesforce_contact_add_with_valid_args(
        self,
        mock_salesforce,
        generate_contact: EditContact,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_contact: Generated contact data
        """
        repository = ContactRepository(mock_salesforce)

        repository.add(generate_contact.as_values_only_dict())

        assert mock_salesforce.Contact.create.called
        assert mock_salesforce.Contact.create.call_args == mock.call(
            generate_contact.as_values_only_dict(),
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_delete_calls_salesforce_contact_delete_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test delete calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.delete(expected_record_id)

        assert mock_salesforce.Contact.delete.called
        assert mock_salesforce.Contact.delete.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_true_when_query_response_succeeds(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        success_query_response = create_success_query_response(
            'Contact',
            expected_record_id,
        )

        with mock.patch(
            'datahub.bed_api.repositories.ContactRepository.query',
            return_value=success_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is True

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_false_when_query_response_fails(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        failed_query_response = create_fail_query_response()

        with mock.patch(
            'datahub.bed_api.repositories.ContactRepository.query',
            return_value=failed_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is False

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_calls_salesforce_contact_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.get(expected_record_id)

        assert mock_salesforce.Contact.get.called
        assert mock_salesforce.Contact.get.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_by_calls_salesforce_contact_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get_by calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_field = 'test_record_field'
        expected_record_id = 'test_record_id'

        repository.get_by(expected_record_field, expected_record_id)

        assert mock_salesforce.Contact.get_by_custom_id.called
        assert mock_salesforce.Contact.get_by_custom_id.call_args == mock.call(
            expected_record_field,
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_update_calls_salesforce_contact_update_with_valid_args(
        self,
        mock_salesforce,
        generate_contact: EditContact,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_contact: Generated contact data
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        generate_contact.Id = expected_record_id

        repository.update(expected_record_id, generate_contact.as_values_only_dict())

        assert mock_salesforce.Contact.update.called
        assert mock_salesforce.Contact.update.call_args == mock.call(
            'test_record_id',
            generate_contact.as_values_only_dict(),
        )


class TestAccountRepositoryShould:
    """Unit tests for AccountRepository"""

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_add_calls_salesforce_contact_add_with_valid_args(
        self,
        mock_salesforce,
        generate_account: EditAccount,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_account: Generated account data
        """
        repository = AccountRepository(mock_salesforce)

        repository.add(generate_account.as_values_only_dict())

        assert mock_salesforce.Account.create.called
        assert mock_salesforce.Account.create.call_args == mock.call(
            generate_account.as_values_only_dict(),
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_delete_calls_salesforce_account_delete_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test delete calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.delete(expected_record_id)

        assert mock_salesforce.Account.delete.called
        assert mock_salesforce.Account.delete.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_true_when_query_response_succeeds(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        success_query_response = create_success_query_response(
            'Account',
            expected_record_id,
        )

        with mock.patch(
            'datahub.bed_api.repositories.AccountRepository.query',
            return_value=success_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is True

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_false_when_query_response_fails(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        failed_query_response = create_fail_query_response()

        with mock.patch(
            'datahub.bed_api.repositories.AccountRepository.query',
            return_value=failed_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is False

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_calls_salesforce_account_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.get(expected_record_id)

        assert mock_salesforce.Account.get.called
        assert mock_salesforce.Account.get.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_by_calls_salesforce_account_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get_by calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_field = 'test_record_field'
        expected_record_id = 'test_record_id'

        repository.get_by(expected_record_field, expected_record_id)

        assert mock_salesforce.Account.get_by_custom_id.called
        assert mock_salesforce.Account.get_by_custom_id.call_args == mock.call(
            expected_record_field,
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_update_calls_salesforce_account_update_with_valid_args(
        self,
        mock_salesforce,
        generate_account: EditContact,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_account: Generated account data
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        generate_account.Id = expected_record_id

        repository.update(expected_record_id, generate_account.as_values_only_dict())

        assert mock_salesforce.Account.update.called
        assert mock_salesforce.Account.update.call_args == mock.call(
            'test_record_id',
            generate_account.as_values_only_dict(),
        )


class TestEventRepositoryShould:
    """Unit tests for EventRepository"""

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_add_calls_salesforce_event_add_with_valid_args(
        self,
        mock_salesforce,
        generate_event: EditEvent,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_event: Generated event data
        """
        repository = EventRepository(mock_salesforce)

        repository.add(generate_event.as_values_only_dict())

        assert mock_salesforce.Event__c.create.called
        assert mock_salesforce.Event__c.create.call_args == mock.call(
            generate_event.as_values_only_dict(),
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_delete_calls_salesforce_event_delete_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test delete calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.delete(expected_record_id)

        assert mock_salesforce.Event__c.delete.called
        assert mock_salesforce.Event__c.delete.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_true_when_query_response_succeeds(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        success_query_response = create_success_query_response(
            'Event__c',
            expected_record_id,
        )

        with mock.patch(
            'datahub.bed_api.repositories.EventRepository.query',
            return_value=success_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is True

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_false_when_query_response_fails(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        failed_query_response = create_fail_query_response()

        with mock.patch(
            'datahub.bed_api.repositories.EventRepository.query',
            return_value=failed_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is False

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_calls_salesforce_event_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.get(expected_record_id)

        assert mock_salesforce.Event__c.get.called
        assert mock_salesforce.Event__c.get.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_by_calls_salesforce_event_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get_by calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventRepository(mock_salesforce)
        expected_record_field = 'test_record_field'
        expected_record_id = 'test_record_id'

        repository.get_by(expected_record_field, expected_record_id)

        assert mock_salesforce.Event__c.get_by_custom_id.called
        assert mock_salesforce.Event__c.get_by_custom_id.call_args == mock.call(
            expected_record_field,
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_update_calls_salesforce_event_update_with_valid_args(
        self,
        mock_salesforce,
        generate_event: EditEvent,
    ):
        """
        Test update calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_event: Generated event data
        """
        repository = EventRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        generate_event.Id = expected_record_id

        repository.update(expected_record_id, generate_event.as_values_only_dict())

        assert mock_salesforce.Event__c.update.called
        assert mock_salesforce.Event__c.update.call_args == mock.call(
            'test_record_id',
            generate_event.as_values_only_dict(),
        )


class TestEventAttendeeRepositoryShould:
    """Unit tests for EventAttendeeRepository"""

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_add_calls_salesforce_event_attendee_add_with_valid_args(
        self,
        mock_salesforce,
        generate_event_attendee: EditEventAttendee,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_event_attendee: Generated event atttendee data
        """
        repository = EventAttendeeRepository(mock_salesforce)

        repository.add(generate_event_attendee.as_values_only_dict())

        assert mock_salesforce.Event_Attendee__c.create.called
        assert mock_salesforce.Event_Attendee__c.create.call_args == mock.call(
            generate_event_attendee.as_values_only_dict(),
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_delete_calls_salesforce_event_attendee_delete_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test delete calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventAttendeeRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.delete(expected_record_id)

        assert mock_salesforce.Event_Attendee__c.delete.called
        assert mock_salesforce.Event_Attendee__c.delete.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_true_when_query_response_succeeds(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventAttendeeRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        success_query_response = create_success_query_response(
            'Event_Attendee__c',
            expected_record_id,
        )

        with mock.patch(
            'datahub.bed_api.repositories.EventAttendeeRepository.query',
            return_value=success_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is True

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_false_when_query_response_fails(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventAttendeeRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        failed_query_response = create_fail_query_response()

        with mock.patch(
            'datahub.bed_api.repositories.EventAttendeeRepository.query',
            return_value=failed_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is False

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_calls_salesforce_event_attendee_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventAttendeeRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.get(expected_record_id)

        assert mock_salesforce.Event_Attendee__c.get.called
        assert mock_salesforce.Event_Attendee__c.get.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_by_calls_salesforce_event_attendee_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get_by calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventAttendeeRepository(mock_salesforce)
        expected_record_field = 'test_record_field'
        expected_record_id = 'test_record_id'

        repository.get_by(expected_record_field, expected_record_id)

        assert mock_salesforce.Event_Attendee__c.get_by_custom_id.called
        assert mock_salesforce.Event_Attendee__c.get_by_custom_id.call_args == mock.call(
            expected_record_field,
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_update_calls_salesforce_event_attendee_update_with_valid_args(
        self,
        mock_salesforce,
        generate_event_attendee: EditEventAttendee,
    ):
        """
        Test update calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_event_attendee: Generated event attendee data
        """
        repository = EventAttendeeRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        generate_event_attendee.Id = expected_record_id

        repository.update(expected_record_id, generate_event_attendee.as_values_only_dict())

        assert mock_salesforce.Event_Attendee__c.update.called
        assert mock_salesforce.Event_Attendee__c.update.call_args == mock.call(
            'test_record_id',
            generate_event_attendee.as_values_only_dict(),
        )

import pytest
from dateutil import parser
from simple_salesforce import format_soql

from datahub.bed_api.constants import ContactQuery, EventQuery
from datahub.bed_api.models import (
    EditAccount,
    EditContact,
    EditEvent,
    EditEventAttendee,
)
from datahub.bed_api.tests.test_utils import (
    assert_all_data_exists_on_bed,
    delete_and_assert_deletion,
    NOT_BED_INTEGRATION_TEST_READY,
)


@pytest.mark.salesforce_test
@pytest.mark.skipif(
    NOT_BED_INTEGRATION_TEST_READY,
    reason='BED security configuration missing from env file',
)
class TestIntegrationEventRepositoryShould:
    """
    Integration Test Event Repositories as Event
    NOTE: Integration Tests needing BED configuration within
    .env - see Vault for valid sandbox only settings
        BED_USERNAME
        BED_PASSWORD
        BED_SECURITY_TOKEN
        BED_IS_SANDBOX
    """

    def test_fuzz_on_crud_operations_utilising(
        self,
        event_repository,
        faker,
        generate_event: EditEvent,
    ):
        """
        Test BedFactory integration with the contact and account repositories
        sampling all functions in an idempotent way, generating potential test
        data for unit tests
        :param event_repository: EventRepository fixture
        :param faker: Faker library for generating data
        :param generate_event: New event record generated with faker data
        """
        event_id = None
        try:
            # CREATE event checking data and that the record exists
            event_id = self.create_and_assert_event(event_repository, generate_event)
            generate_event.Id = event_id

            # UPDATE event checking the patch
            self.update_and_assert_event(event_id, event_repository, faker, generate_event)

            # QUERY and QUERY NEXT testing PAGINATION concepts and COUNT Query constructs
            self.assert_and_query_paginated_data(event_repository, generate_event)
        finally:
            # Delete to clean up integration test
            delete_and_assert_deletion(
                event_repository,
                event_id,
            )

    def update_and_assert_event(
        self,
        event_id,
        event_repository,
        faker,
        event,
    ):
        """
        Update and assert the event is updated with the data on Salesforce
        :param event_id: Event id
        :param event_repository: EventRepository fixture
        :param faker: Faker library for generating data
        :param event: New event record generated with faker data
        """
        event.Description__c = faker.text()
        update_response = event_repository.update(
            event_id,
            {
                'Description__c': event.Description__c,
            },
        )
        assert update_response is not None
        assert update_response == 204
        event_data_response = event_repository.get(event_id)
        assert event_data_response is not None
        assert event_data_response['Description__c'] == event.Description__c

    def assert_and_query_paginated_data(self, event_repository, event):
        """
        Uses the repository query and query_more to test querying and paginating
        data
        :param event_repository: EventRepository fixture
        :param event: New event record generated with faker data
        """
        # date_filter = date(1976, 2, 11)
        date_filter = parser.parse(event.Date__c)
        query = format_soql(
            EventQuery.get_event_id_by_date.value.sql,
            date=date_filter.date(),
            limit=100,  # take
            offset=0,  # skip
        )
        query_response = event_repository.query(query)
        self.assert_query_response(query_response)
        self.assert_records_for_ids(query_response)
        if 'nextRecordUrl' in query_response:
            next_records_url = query_response['nextRecordUrl']
            self.assert_and_query_next(event_repository, next_records_url)
        self.assert_count_query(date_filter, event_repository)

    def assert_count_query(self, date_filter, event_repository):
        """
        Validates and demonstrates a count
        :param date_filter: Filter by data from event
        :param event_repository: EventRepository fixture
        """
        query = format_soql(
            EventQuery.count_event_by_date.value.sql,
            date=date_filter.date(),
        )
        # Count data
        count_response = event_repository.query(query)
        self.assert_query_response(count_response)
        assert count_response['records'][0]['expr0'] >= 1

    def assert_and_query_next(self, event_repository, next_records_url):
        """
        Validate the next query and show an example of the usage
        :param event_repository: EventRepository fixture
        :param next_records_url: The url generated from the original query
        """
        next_query_response = event_repository.query_next(
            next_records_url,
            True,
        )
        self.assert_query_response(next_query_response)
        self.assert_records_for_ids(next_query_response)

    def assert_records_for_ids(self, query_response):
        """
        Validates the record data for id values assigned
        :param query_response: Typical query response object
        returned from Salesforce
        """
        for item in query_response['records']:
            assert item['Id'] is not None

    def assert_query_response(self, query_response):
        """
        Validates the Query response comes back with expected data
        :param query_response: Typical query response object
        returned from Salesforce
        """
        assert query_response is not None
        assert query_response['totalSize'] >= 1
        assert query_response['records'] is not None

    def create_and_assert_event(
        self,
        event_repository,
        event: EditEvent,
    ):
        """
        Create event on Salesforce and validate the data passed is generated as expected
        :param event_repository: EventRepository fixture
        :param event: New event record generated with faker data
        :return: New event id
        """
        event_response = event_repository.add(
            event.as_values_only_dict(),
        )
        assert event_response is not None
        assert event_response['success'] is True
        event_id = event_response['id']
        assert event_id is not None
        assert_all_data_exists_on_bed(event, event_id, event_repository)
        return event_id


@pytest.mark.salesforce_test
@pytest.mark.skipif(
    NOT_BED_INTEGRATION_TEST_READY,
    reason='BED security configuration missing from env file',
)
class TestIntegrationContactWithEventAndAccountShould:
    """
    Integration Test Contact and Account Repositories as Contact is dependent on an Account
    NOTE: Integration Tests needing BED configuration within
    .env - see Vault for valid sandbox only settings
        BED_USERNAME
        BED_PASSWORD
        BED_SECURITY_TOKEN
        BED_IS_SANDBOX
    """

    def test_fuzz_on_crud_operations_utilising(
        self,
        contact_repository,
        account_repository,
        event_repository,
        event_attendee_repository,
        faker,
        generate_account: EditAccount,
        generate_contact: EditContact,
        generate_event: EditEvent,
        generate_event_attendee: EditEventAttendee,
    ):
        """
        Test BedFactory integration with the contact and account repositories
        sampling all functions in an idempotent way, generating potential test
        data for unit tests
        :param contact_repository: ContactRepository fixture
        :param account_repository: AccountRepository fixture
        :param event_repository: EventRepository fixture
        :param event_attendee_repository: EventAttendeeRepository fixture
        :param faker: Faker library for generating data
        :param generate_account: New account record generated with faker data
        :param generate_contact: New contact record generated with faker data
        :param generate_event: New event record generated with faker data
        :param generate_event_attendee: New event attendee record generated with faker data
        """
        new_contact_id = None
        new_account_id = None
        new_event_id = None
        new_event_attendee_id = None
        try:
            # Create a new account / organization / company
            new_account_id = self.generate_and_assert_account(
                account_repository,
                generate_account,
            )

            # Create contact
            generate_contact.AccountId = new_account_id
            new_contact_id = self.generate_and_assert_contact(
                contact_repository,
                generate_contact,
            )

            #  Update Contact
            self.update_and_assert_contact(
                contact_repository,
                new_contact_id,
                faker,
            )

            #  Create event
            new_event_id = self.generate_assert_event(event_repository, generate_event)

            #  Link Contact as event attendee
            new_event_attendee_id = self.generate_and_assert_event_attendee(
                event_attendee_repository,
                generate_event_attendee,
                new_contact_id,
                new_event_id,
            )
        finally:
            #  Clean up generated data
            delete_and_assert_deletion(
                contact_repository,
                new_contact_id,
            )
            delete_and_assert_deletion(
                account_repository,
                new_account_id,
            )
            delete_and_assert_deletion(
                event_attendee_repository,
                new_event_attendee_id,
            )
            delete_and_assert_deletion(
                event_repository,
                new_event_id,
            )

    def generate_and_assert_event_attendee(
            self,
            event_attendee_repository,
            event_attendee,
            contact_id,
            event_id,
    ):
        """
        Create event attendee assigning a contact and event to marry the two
        :param event_attendee_repository: EventAttendeeRepository fixture
        :param event_attendee: New event attendee record generated with faker data
        :param contact_id: New contact id
        :param event_id:  New event id
        :return: New event attendee id
        """
        event_attendee.Event__c = event_id
        event_attendee.Attendee__c = contact_id
        event_attendee_response = event_attendee_repository.add(
            event_attendee.as_values_only_dict(),
        )
        assert event_attendee_response is not None
        assert event_attendee_response['success'] is True
        event_attendee_id = event_attendee_response['id']
        assert event_attendee_id is not None
        assert_all_data_exists_on_bed(
            event_attendee,
            event_attendee_id,
            event_attendee_repository,
        )
        return event_attendee_id

    def generate_assert_event(self, event_repository, event):
        """
        Generate a new event and assert success
        :param event_repository: EventRepository fixture
        :param event: New event record generated with faker data
        :return: New event id
        """
        event_response = event_repository.add(
            event.as_values_only_dict(),
        )
        assert event_response is not None
        assert event_response['success'] is True
        event_id = event_response['id']
        assert event_id is not None
        assert_all_data_exists_on_bed(
            event,
            event_id,
            event_repository,
        )
        return event_id

    def update_and_assert_contact(
        self,
        contact_repository,
        new_contact_id,
        faker,
    ):
        """
        Update the contact with basic notes testing update
        :param contact_repository: ContactRepository fixture
        :param new_contact_id: Contact id to update
        :param faker: Faker library
        """
        # Example using original edit object sending all values
        # contact.Notes__c = 'Integration Test Notes - Update'
        # update_contact_response = repository.update(
        #     f'Id/{contact_id}', contact.as_values_only_dict())
        notes_update = faker.text(max_nb_chars=100)
        update_contact_response = contact_repository.update(
            f'Id/{new_contact_id}',
            dict(Notes__c=notes_update),
        )
        assert update_contact_response is not None
        assert update_contact_response == 204

        contact_check = contact_repository.query(
            format_soql(
                ContactQuery.get_notes_by_id.value.sql,
                id=new_contact_id,
            ),
        )
        assert contact_check is not None
        assert contact_check['totalSize'] == 1
        assert contact_check['done'] is True
        assert contact_check['records'][0]['Id'] == new_contact_id
        assert contact_check['records'][0]['Notes__c'] == notes_update

    def generate_and_assert_contact(
        self,
        contact_repository,
        contact: EditContact,
    ):
        """
        Create Account data on Salesforce testing as many ContactRepository
        Methods as possible
        :param contact_repository: ContactRepository fixture
        :param contact: Random Generated Contact
        :return: new contact id
        """
        contact_add_response = contact_repository.add(contact.as_values_only_dict())
        assert contact_add_response is not None
        assert contact_add_response['success'] is True
        contact_id = contact_add_response['id']
        contact.Id = contact_id
        assert_all_data_exists_on_bed(contact, contact_id, contact_repository)
        return contact_id

    def generate_and_assert_account(
        self,
        account_repository,
        account: EditAccount,
    ):
        """
        Create Account Data on Salesforce using dynamic data
        :param account_repository: AccountRepository fixture
        :param account: New account record generated with faker data
        :return: Account Id
        """
        account_add_response = account_repository.add(account.as_values_only_dict())
        assert account_add_response is not None
        assert account_add_response['success'] is True
        account_id = account_add_response['id']
        assert account_id is not None
        account.Id = account_id
        assert_all_data_exists_on_bed(account, account_id, account_repository)
        return account_id

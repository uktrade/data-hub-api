from dateutil import parser
import pytest
from simple_salesforce import format_soql

from datahub.bed_api.constants import ContactQuery, EventQuery
from datahub.bed_api.models import (
    EditAccount,
    EditContact,
    EditEvent,
)
from datahub.bed_api.tests.test_utils import NOT_BED_INTEGRATION_TEST_READY


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

    def test_crud_operations_event_utilising(
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
            if event_id:
                self.delete_and_assert_event_deletion(
                    event_repository,
                    event_id,
                )

    def update_and_assert_event(self, event_id, event_repository, faker, event):
        event.Description__c = faker.text()
        update_response = event_repository.update(
            event_id,
            {
                'Description__c': event.Description__c
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
        assert query_response['done'] is True
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
        event.Id = event_id
        self.assert_all_event_data(event, event_repository)
        return event_id

    def assert_all_event_data(self, event, event_repository):
        """
        Verify all data added onto BED or Salesforce and check the record exists
        :param event: New event record generated with faker data
        :param event_repository:
        :param event_repository: EventRepository fixture
        """
        event_exists = event_repository.exists(event.Id)
        assert event_exists is True
        event_data = event_repository.get(event.Id)
        for key, value in event.as_values_only_dict().items():
            assert event_data[key] == value

    def delete_and_assert_event_deletion(
        self,
        event_repository,
        event_id,
    ):
        """
        Delete generated account from the database
        :param event_repository: EventRepository fixture
        :param event_id: Account id to delete
        """
        delete_event_response = event_repository.delete(event_id)
        assert delete_event_response is not None
        assert delete_event_response == 204
        exists = event_repository.exists(event_id)
        assert exists is False


@pytest.mark.salesforce_test
@pytest.mark.skipif(
    NOT_BED_INTEGRATION_TEST_READY,
    reason='BED security configuration missing from env file',
)
class TestIntegrationContactWithAccountRepositoryShould:
    """
    Integration Test Contact and Account Repositories as Contact is dependent on an Account
    NOTE: Integration Tests needing BED configuration within
    .env - see Vault for valid sandbox only settings
        BED_USERNAME
        BED_PASSWORD
        BED_SECURITY_TOKEN
        BED_IS_SANDBOX
    """

    def test_crud_utilising(
        self,
        contact_repository,
        account_repository,
        faker,
        generate_account: EditAccount,
        generate_contact: EditContact,
    ):
        """
        Test BedFactory integration with the contact and account repositories
        sampling all functions in an idempotent way, generating potential test
        data for unit tests
        :param contact_repository: ContactRepository fixture
        :param account_repository: AccountRepository fixture
        :param faker: Faker library for generating data
        :param generate_account: New account record generated with faker data
        :param generate_contact: New contact record generated with faker data
        """
        new_contact_id = None
        new_account_id = None
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
            self.update_and_assert_contact(contact_repository, new_contact_id, faker)

            # TODO Update Account

        finally:
            #  Clean up generated data
            if new_contact_id:
                self.delete_and_assert_contact_deletion(
                    contact_repository,
                    new_contact_id,
                )
            if new_account_id:
                self.delete_and_assert_account_deletion(
                    account_repository,
                    new_account_id,
                )

    def delete_and_assert_account_deletion(
        self,
        account_repository,
        account_id,
    ):
        """
        Delete generated account from the database
        :param account_repository: AccountRepository fixture
        :param account_id: Account id to delete
        """
        delete_account_response = account_repository.delete(account_id)
        assert delete_account_response is not None
        assert delete_account_response == 204
        exists = account_repository.exists(account_id)
        assert exists is False

    def delete_and_assert_contact_deletion(
        self,
        contact_repository,
        contact_id,
    ):
        """
        Delete generated contact from the database
        :param contact_repository: ContactRepository fixture
        :param contact_id: Contact id to delete
        """
        delete_contact_response = contact_repository.delete(contact_id)
        assert delete_contact_response is not None
        assert delete_contact_response == 204
        exists = contact_repository.exists(contact_id)
        assert exists is False

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
        # update_contact_response = contact_repository.update(
        #     f'Id/{new_contact_id}', contact.as_values_only_dict())
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
        self.assert_all_contact_data(contact, contact_repository)
        return contact_id

    def assert_all_contact_data(self, contact, contact_repository):
        """
        Verify contact exists on Salesforce and the data is the same as the
        data used to generate teh contact
        :param contact: Random Generated Contact
        :param contact_repository: ContactRepository fixture
        """
        contact_exists = contact_repository.exists(contact.Id)
        assert contact_exists is True
        contact_data = contact_repository.get_by(
            'Datahub_ID__c',
            contact.Datahub_ID__c,
        )
        for key, value in contact.as_values_only_dict().items():
            assert contact_data[key] == value

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
        self.assert_all_account_data(account, account_repository)
        return account_id

    def assert_all_account_data(self, account, account_repository):
        """
        Verify all data added onto BED or Salesforce and check the record exists
        :param account: New account record generated with faker data
        :param account_repository:
        :param account_repository: AccountRepository fixture
        """
        account_exists = account_repository.exists(account.Id)
        assert account_exists is True
        account_data = account_repository.get(account.Id)
        for key, value in account.as_values_only_dict().items():
            assert account_data[key] == value

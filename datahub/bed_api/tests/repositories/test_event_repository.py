from unittest import mock

from datahub.bed_api.entities import Event
from datahub.bed_api.repositories import EventRepository
from datahub.bed_api.tests.test_utils import (
    create_fail_query_response,
    create_success_query_response,
)


class TestEventRepositoryShould:
    """Unit tests for EventRepository"""

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_add_calls_salesforce_event_add_with_valid_args(
        self,
        mock_salesforce,
        event: Event,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param event: Generated event data
        """
        repository = EventRepository(mock_salesforce)

        repository.add(event.as_values_only_dict())

        assert mock_salesforce.Event__c.create.called
        assert mock_salesforce.Event__c.create.call_args == mock.call(
            event.as_values_only_dict(),
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
    def test_get_by_datahub_id_calls_salesforce_contact_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get_by calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = EventRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.get_by_datahub_id(expected_record_id)

        assert mock_salesforce.Event__c.get_by_custom_id.called
        assert mock_salesforce.Event__c.get_by_custom_id.call_args == mock.call(
            'Datahub_ID__c',
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_update_calls_salesforce_event_update_with_valid_args(
        self,
        mock_salesforce,
        event: Event,
    ):
        """
        Test update calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param event: Generated event data
        """
        repository = EventRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        event.id = expected_record_id

        repository.update(expected_record_id, event.as_values_only_dict())

        assert mock_salesforce.Event__c.update.called
        assert mock_salesforce.Event__c.update.call_args == mock.call(
            'test_record_id',
            event.as_values_only_dict(),
        )

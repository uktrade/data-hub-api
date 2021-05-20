from unittest import mock

import pytest

from datahub.bed_api.repositories import SalesforceRepository


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

from unittest import mock

from datahub.bed_api.repositories import ReadRepository


class TestSalesforceReadRepositoryShould:
    """
    Unit tests for Base ReadRepository for functionality
    that applies to all repositories like query and
    query next
    """

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_query_calls_salesforce_query_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test query_more calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ReadRepository(mock_salesforce)
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
        repository = ReadRepository(mock_salesforce)
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

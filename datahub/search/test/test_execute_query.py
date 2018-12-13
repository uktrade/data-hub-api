from unittest import mock

from datahub.search.company.apps import CompanySearchApp
from datahub.search.execute_query import execute_autocomplete_query


class TestExecuteQueryBuilder:
    """Tests for executing search queries."""

    def test_successful_execute_autocomplete_search_query(self):
        """Test for executing an autocomplete search query."""
        fake_result = [{'_source': []}]
        suggest = mock.Mock(autocomplete=[mock.Mock(options=fake_result)])
        mocked_es_response = mock.MagicMock(suggest=suggest)
        with mock.patch('elasticsearch_dsl.Search.execute') as mock_es_execute:
            mock_es_execute.return_value = mocked_es_response
            result = execute_autocomplete_query(CompanySearchApp.es_model, 'hello', 10)
        assert result == fake_result
        assert mock_es_execute.called

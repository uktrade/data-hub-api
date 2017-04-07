from unittest import mock

from datahub.es.utils import get_elasticsearch_client


@mock.patch('datahub.es.utils.Elasticsearch')
def test_get_elasticsearch_client(mock_es, settings):
    """Test get ES client without authentication."""
    settings.HEROKU = False
    settings.ES_HOST = 'foo'
    get_elasticsearch_client()
    mock_es.assert_called_once_with([{'port': 9200, 'host': 'foo'}])


@mock.patch('datahub.es.utils.Elasticsearch')
def test_get_elasticsearch_client_heroku(mock_es, settings):
    """Test get ES client with Heroku authentication."""
    settings.HEROKU = True
    settings.ES_HOST = 'https://foo:bar@test.com'
    get_elasticsearch_client()
    mock_es.assert_called_once_with([{'host': 'test.com', 'use_ssl': True, 'port': 9200, 'http_auth': ('foo', 'bar')}])

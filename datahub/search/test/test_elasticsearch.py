from unittest import mock

import pytest

from .. import elasticsearch


@mock.patch('datahub.search.elasticsearch.es_bulk')
def test_bulk(es_bulk, mock_es_client):
    """Tests detailed company search."""
    actions = []
    chunk_size = 10
    elasticsearch.bulk(actions=actions, chunk_size=chunk_size)

    es_bulk.assert_called_with(mock_es_client.return_value, actions=actions, chunk_size=chunk_size)


@mock.patch('datahub.search.elasticsearch.settings')
@mock.patch('datahub.search.elasticsearch.connections')
def test_configure_connection(connections, settings):
    """Tests if Heroku connection is configured."""
    settings.HEROKU = True
    settings.ES_USE_AWS_AUTH = False
    settings.ES_URL = 'https://login:password@test:1234'
    connections.configure.return_value = {}

    elasticsearch.configure_connection()

    connections.configure.assert_called_with(default={
        'hosts': [settings.ES_URL],
        'verify_certs': settings.ES_VERIFY_CERTS
    })


def test_configure_index_creates_index_if_it_doesnt_exist(mock_es_client):
    """Test that configure_index() creates the index when it doesn't exist."""
    index = 'test-index'
    index_settings = {
        'testsetting1': 'testval1'
    }
    connection = mock_es_client.return_value
    connection.indices.exists.return_value = False
    elasticsearch.configure_index(index, index_settings=index_settings)
    connection.indices.create.assert_called_once_with(
        index='test-index',
        body={
            'settings': {
                'testsetting1': 'testval1',
                'analysis': {
                    'analyzer': {
                        'lowercase_keyword_analyzer': {
                            'tokenizer': 'keyword',
                            'filter': ['lowercase'],
                            'type': 'custom'
                        },
                        'trigram_analyzer': {
                            'tokenizer': 'trigram',
                            'char_filter': ['special_chars'],
                            'filter': ['lowercase'],
                            'type': 'custom'
                        },
                        'english_analyzer': {
                            'tokenizer': 'standard',
                            'filter': [
                                'english_possessive_stemmer',
                                'lowercase',
                                'english_stop',
                                'english_stemmer'
                            ],
                            'type': 'custom'
                        },
                        'lowercase_analyzer': {
                            'tokenizer': 'standard',
                            'filter': ['lowercase'],
                            'type': 'custom'
                        }
                    },
                    'tokenizer': {
                        'trigram': {
                            'min_gram': 3,
                            'max_gram': 3,
                            'token_chars': ('letter', 'digit'),
                            'type': 'nGram'
                        }
                    },
                    'char_filter': {
                        'special_chars': {
                            'mappings': ('-=>',),
                            'type': 'mapping'}
                    },
                    'filter': {
                        'english_possessive_stemmer': {
                            'language': 'possessive_english',
                            'type': 'stemmer'
                        },
                        'english_stop': {
                            'stopwords': '_english_', 'type': 'stop'
                        },
                        'english_stemmer': {
                            'language': 'english', 'type': 'stemmer'
                        }
                    }
                }
            }
        }
    )


def test_configure_index_doesnt_create_index_if_it_exists(mock_es_client):
    """Test that configure_index() doesn't create the index when it already exists."""
    index = 'test-index'
    index_settings = {
        'testsetting1': 'testval1'
    }
    connection = mock_es_client.return_value
    connection.indices.exists.return_value = True
    elasticsearch.configure_index(index, index_settings=index_settings)
    connection.indices.create.assert_not_called()


@pytest.mark.django_db
@mock.patch('datahub.search.elasticsearch.configure_index')
@mock.patch('datahub.search.elasticsearch.get_search_apps')
def test_init_es(get_search_apps_mock, configure_index_mock):
    """Test that init_es() calls configure_index() and init_es() on each search app."""
    apps = [mock.Mock(), mock.Mock()]
    get_search_apps_mock.return_value = apps

    elasticsearch.init_es()

    configure_index_mock.assert_called_once()
    apps[0].init_es.assert_called_once()
    apps[1].init_es.assert_called_once()

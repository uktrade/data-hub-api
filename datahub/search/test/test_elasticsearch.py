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


@pytest.mark.parametrize('expected', (True, False))
def test_index_exists(mock_es_client, expected):
    """Tests that `index_exists` returns True if the index exists, False otherwise."""
    index_name = 'test'

    connection = mock_es_client.return_value
    connection.indices.exists.return_value = expected

    assert elasticsearch.index_exists(index_name) == expected
    connection.indices.exists.assert_called_with(index_name)


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


def test_creates_index(mock_es_client):
    """Test creates_index()."""
    index = 'test-index'
    index_settings = {
        'testsetting1': 'testval1'
    }
    connection = mock_es_client.return_value
    elasticsearch.create_index(index, index_settings=index_settings)
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


def test_delete_index(mock_es_client):
    """Test delete_index()."""
    index = 'test-index'
    client = mock_es_client.return_value
    elasticsearch.delete_index(index)
    client.indices.delete.assert_called_once_with(index)


def test_get_indices_for_alias(mock_es_client):
    """Test get_indices_for_alias()."""
    alias = 'test-index'
    client = mock_es_client.return_value
    client.indices.get_alias.return_value = {
        'index1': {'aliases': {'alias1': {}}},
        'index2': {'aliases': {'alias2': {}}},
    }
    assert elasticsearch.get_indices_for_alias(alias) == {'index1', 'index2'}
    client.indices.get_alias.assert_called_with(name=alias)


def test_get_aliases_for_index(mock_es_client):
    """Test get_aliases_for_index()."""
    index = 'test-index'
    client = mock_es_client.return_value
    client.indices.get_alias.return_value = {
        index: {
            'aliases': {
                'alias1': {},
                'alias2': {},
            }
        }
    }
    assert elasticsearch.get_aliases_for_index(index) == {'alias1', 'alias2'}
    client.indices.get_alias.assert_called_with(index=index)


@pytest.mark.parametrize('expected', (True, False))
def test_alias_exists(mock_es_client, expected):
    """Test alias_exists()."""
    index_name = 'test-index'

    client = mock_es_client.return_value
    client.indices.exists_alias.return_value = expected

    assert elasticsearch.alias_exists(index_name) == expected
    client.indices.exists_alias.assert_called_with(name=index_name)


@pytest.mark.parametrize(
    'add_actions,remove_actions,expected_body',
    (
        (
            (
                (),
                (
                    ('test-alias', ('index1', 'index2')),
                ),
                {
                    'actions': [{
                        'remove': {
                            'alias': 'test-alias',
                            'indices': ['index1', 'index2'],
                        }
                    }]
                }
            ),
            (
                (
                    ('test-alias', ('index1', 'index2')),
                ),
                (),
                {
                    'actions': [{
                        'add': {
                            'alias': 'test-alias',
                            'indices': ['index1', 'index2'],
                        }
                    }]
                }
            ),
            (
                (
                    ('test-alias', ('index1', 'index2')),
                ),
                (
                    ('test-alias-2', ('index3', 'index4')),
                ),
                {
                    'actions': [
                        {
                            'add': {
                                'alias': 'test-alias',
                                'indices': ['index1', 'index2'],
                            }
                        },
                        {
                            'remove': {
                                'alias': 'test-alias-2',
                                'indices': ['index3', 'index4'],
                            }
                        },
                    ]
                }
            ),
        )
    )
)
def test_update_alias(mock_es_client, add_actions, remove_actions, expected_body):
    """Test get_aliases_for_index()."""
    client = mock_es_client.return_value
    with elasticsearch.start_alias_transaction() as alias_transaction:
        for action in add_actions:
            alias_transaction.add_indices_to_alias(action[0], action[1])
        for action in remove_actions:
            alias_transaction.remove_indices_from_alias(action[0], action[1])
    client.indices.update_aliases.assert_called_with(body=expected_body)

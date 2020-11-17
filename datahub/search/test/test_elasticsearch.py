from unittest import mock

import pytest
from django.conf import settings
from elasticsearch_dsl import Keyword, Mapping

from datahub.search import elasticsearch


@mock.patch('datahub.search.elasticsearch.es_bulk')
def test_bulk(es_bulk, mock_es_client):
    """Tests detailed company search."""
    actions = []
    chunk_size = 10
    elasticsearch.bulk(actions=actions, chunk_size=chunk_size)

    es_bulk.assert_called_with(
        mock_es_client.return_value,
        actions=actions,
        chunk_size=chunk_size,
        max_chunk_bytes=settings.ES_BULK_MAX_CHUNK_BYTES,
    )


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
    """Test configuration of the connection."""
    settings.ES_URL = 'https://login:password@test:1234'
    connections.configure.return_value = {}

    elasticsearch.configure_connection()

    connections.configure.assert_called_with(default={
        'hosts': [settings.ES_URL],
        'verify_certs': settings.ES_VERIFY_CERTS,
    })


def test_creates_index(monkeypatch, mock_connection_for_create_index):
    """Test creates_index()."""
    monkeypatch.setattr(
        'django.conf.settings.ES_INDEX_SETTINGS',
        {
            'testsetting1': 'testval1',
        },
    )
    mapping = Mapping()
    mapping.field('test-field', Keyword())
    index = 'test-index'
    connection = mock_connection_for_create_index.return_value

    elasticsearch.create_index(index, mapping, alias_names=('alias1', 'alias2'))
    connection.indices.create.assert_called_once_with(
        index='test-index',
        body={
            'settings': {
                'testsetting1': 'testval1',
                'analysis': {
                    'analyzer': {
                        'trigram_analyzer': {
                            'tokenizer': 'trigram',
                            'char_filter': ['special_chars'],
                            'filter': ['lowercase'],
                            'type': 'custom',
                        },
                        'english_analyzer': {
                            'tokenizer': 'standard',
                            'filter': [
                                'english_possessive_stemmer',
                                'lowercase',
                                'english_stop',
                                'english_stemmer',
                            ],
                            'type': 'custom',
                        },
                    },
                    'tokenizer': {
                        'trigram': {
                            'min_gram': 3,
                            'max_gram': 3,
                            'token_chars': ('letter', 'digit'),
                            'type': 'nGram',
                        },
                    },
                    'char_filter': {
                        'special_chars': {
                            'mappings': ('-=>',),
                            'type': 'mapping',
                        },
                    },
                    'filter': {
                        'english_possessive_stemmer': {
                            'language': 'possessive_english',
                            'type': 'stemmer',
                        },
                        'english_stop': {
                            'stopwords': '_english_', 'type': 'stop',
                        },
                        'english_stemmer': {
                            'language': 'english', 'type': 'stemmer',
                        },
                    },
                },
            },
            'aliases': {
                'alias1': {},
                'alias2': {},
            },
            'mappings': {
                'properties': {
                    'test-field': {
                        'type': 'keyword',
                    },
                },
            },
        },
    )


def test_delete_index(mock_es_client):
    """Test delete_index()."""
    index = 'test-index'
    client = mock_es_client.return_value
    elasticsearch.delete_index(index)
    client.indices.delete.assert_called_once_with(index)


@pytest.mark.parametrize(
    'aliases,response,result',
    (
        (
            ('alias1',),
            {
                'index1': {'aliases': {'alias1': {}}},
            },
            [{'index1'}],
        ),
        (
            ('alias2',),
            {
                'index2': {'aliases': {'alias2': {}}},
            },
            [{'index2'}],
        ),
        (
            ('alias1', 'alias2'),
            {
                'index1': {'aliases': {'alias1': {}}},
                'index2': {'aliases': {'alias2': {}}},
            },
            [{'index1'}, {'index2'}],
        ),
    ),
    ids=['(alias1,)', '(alias1,alias2)', '(alias2,)'],
)
def test_get_indices_for_aliases(mock_es_client, aliases, response, result):
    """Test get_indices_for_aliases()."""
    client = mock_es_client.return_value
    client.indices.get_alias.return_value = response
    assert elasticsearch.get_indices_for_aliases(*aliases) == result


def test_get_aliases_for_index(mock_es_client):
    """Test get_aliases_for_index()."""
    index = 'test-index'
    client = mock_es_client.return_value
    client.indices.get_alias.return_value = {
        index: {
            'aliases': {
                'alias1': {},
                'alias2': {},
            },
        },
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
                        },
                    }],
                },
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
                        },
                    }],
                },
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
                            },
                        },
                        {
                            'remove': {
                                'alias': 'test-alias-2',
                                'indices': ['index3', 'index4'],
                            },
                        },
                    ],
                },
            ),
        )
    ),
)
def test_update_alias(mock_es_client, add_actions, remove_actions, expected_body):
    """Test get_aliases_for_index()."""
    client = mock_es_client.return_value
    with elasticsearch.start_alias_transaction() as alias_transaction:
        for action in add_actions:
            alias_transaction.associate_indices_with_alias(action[0], action[1])
        for action in remove_actions:
            alias_transaction.dissociate_indices_from_alias(action[0], action[1])
    client.indices.update_aliases.assert_called_with(body=expected_body)


def test_create_alias(mock_es_client):
    """Test create_alias()."""
    index_name = 'test-index'
    alias_name = 'test-alias'

    client = mock_es_client.return_value

    elasticsearch.associate_index_with_alias(alias_name, index_name)
    client.indices.put_alias.assert_called_with(index_name, alias_name)

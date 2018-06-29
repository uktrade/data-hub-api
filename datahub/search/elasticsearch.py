from contextlib import contextmanager
from logging import getLogger
from urllib.parse import urlparse

from aws_requests_auth.aws_auth import AWSRequestsAuth
from django.conf import settings
from elasticsearch import RequestsHttpConnection
from elasticsearch.helpers import bulk as es_bulk
from elasticsearch_dsl import analysis, Index
from elasticsearch_dsl.connections import connections


logger = getLogger(__name__)


lowercase_keyword_analyzer = analysis.CustomAnalyzer(
    'lowercase_keyword_analyzer',
    tokenizer='keyword',
    filter=('lowercase',)
)

# Trigram tokenizer enables us to support partial matching
trigram = analysis.tokenizer(
    'trigram',
    'nGram',
    min_gram=3,
    max_gram=3,
    token_chars=('letter', 'digit',)
)

# Filters out "-" so that t-shirt and tshirt can be matched
special_chars = analysis.char_filter('special_chars', 'mapping', mappings=('-=>',))
trigram_analyzer = analysis.CustomAnalyzer(
    'trigram_analyzer',
    tokenizer=trigram,
    char_filter=special_chars,
    filter=('lowercase',),
)

english_possessive_stemmer = analysis.token_filter(
    'english_possessive_stemmer',
    type='stemmer',
    language='possessive_english'
)

english_stemmer = analysis.token_filter(
    'english_stemmer',
    type='stemmer',
    language='english'
)

english_stop = analysis.token_filter(
    'english_stop',
    type='stop',
    stopwords='_english_'
)

english_analyzer = analysis.CustomAnalyzer(
    'english_analyzer',
    tokenizer='standard',
    filter=[
        english_possessive_stemmer,
        'lowercase',
        english_stop,
        english_stemmer,
    ]
)

lowercase_analyzer = analysis.CustomAnalyzer(
    'lowercase_analyzer',
    tokenizer='standard',
    filter=('lowercase',)
)


ANALYZERS = (
    lowercase_keyword_analyzer,
    trigram_analyzer,
    english_analyzer,
    lowercase_analyzer,
)


def configure_connection():
    """Configure Elasticsearch default connection."""
    if settings.ES_USE_AWS_AUTH:
        es_protocol = {
            'http': 80,
            'https': 443
        }
        es_host = urlparse(settings.ES_URL)
        es_port = es_host.port if es_host.port else es_protocol.get(es_host.scheme)
        auth = AWSRequestsAuth(
            aws_access_key=settings.AWS_ELASTICSEARCH_KEY,
            aws_secret_access_key=settings.AWS_ELASTICSEARCH_SECRET,
            aws_host=es_host.netloc,
            aws_region=settings.AWS_ELASTICSEARCH_REGION,
            aws_service='es'
        )
        connections_default = {
            'hosts': [es_host.netloc],
            'port': es_port,
            'use_ssl': settings.ES_USE_SSL,
            'verify_certs': settings.ES_VERIFY_CERTS,
            'http_auth': auth,
            'connection_class': RequestsHttpConnection
        }
    else:
        connections_default = {
            'hosts': [settings.ES_URL],
            'verify_certs': settings.ES_VERIFY_CERTS
        }

    connections.configure(
        default=connections_default
    )


def get_client():
    """Gets an instance of the Elasticsearch client from the connection cache."""
    return connections.get_connection()


def index_exists(index_name):
    """Checks if an index exists."""
    client = get_client()
    return client.indices.exists(index_name)


def create_index(index_name, index_settings=None):
    """Configures Elasticsearch index."""
    index = Index(index_name)
    for analyzer in ANALYZERS:
        index.analyzer(analyzer)

    if index_settings:
        index.settings(**index_settings)
    index.create()


def delete_index(index_name):
    """Deletes an index."""
    logger.info(f'Deleting the {index_name} index...')
    client = get_client()
    client.indices.delete(index_name)


def get_indices_for_alias(alias):
    """Gets the indices referenced by an alias."""
    client = get_client()
    return client.indices.get_alias(name=alias).keys()


def get_indices_for_aliases(*aliases):
    """Gets the indices referenced by one or more aliases."""
    client = get_client()
    alias_to_index_mapping = {alias: set() for alias in aliases}
    index_to_alias_mapping = client.indices.get_alias(name=aliases)

    for index_name, index_properties in index_to_alias_mapping.items():
        for alias in index_properties['aliases']:
            alias_to_index_mapping[alias].add(index_name)

    return [alias_to_index_mapping[alias] for alias in aliases]


def get_aliases_for_index(index):
    """Gets the aliases referencing an index."""
    client = get_client()
    alias_response = client.indices.get_alias(index=index)
    return alias_response[index]['aliases'].keys()


def alias_exists(alias):
    """Checks if an alias exists."""
    client = get_client()
    return client.indices.exists_alias(name=alias)


def delete_alias(alias_name):
    """Deletes an alias entirely (dissociating it from all indices)."""
    logger.info(f'Deleting the {alias_name} alias...')
    client = get_client()
    client.indices.delete_alias('_all', alias_name)


class _AliasUpdater:
    """Helper class for making multiple alias updates atomically."""

    def __init__(self):
        """Initialises the instance with an empty list of pending operations."""
        self.actions = []

    def associate_indices_with_alias(self, alias, indices):
        """Adds a pending operation to associate a new or existing alias with a set of indices."""
        self.actions.append({
            'add': {
                'alias': alias,
                'indices': list(indices)
            }
        })

    def dissociate_indices_from_alias(self, alias, indices):
        """Adds a pending operation to dissociate an existing alias from a set of indices."""
        self.actions.append({
            'remove': {
                'alias': alias,
                'indices': list(indices)
            }
        })

    def commit(self):
        """Commits (flushes) pending operations."""
        client = get_client()
        client.indices.update_aliases(body={
            'actions': self.actions
        })
        self.actions = []


@contextmanager
def start_alias_transaction():
    """Returns a context manager that can be used to update indices atomically."""
    alias_updater = _AliasUpdater()
    yield alias_updater
    alias_updater.commit()


def associate_alias_with_index(alias, index):
    """
    Associates a new or existing alias with an index.

    This is only intended to be a convenience function for simple operations. For more complex
    operations, use start_alias_transaction().
    """
    client = get_client()
    client.indices.put_alias(index, alias)


def bulk(actions=None, chunk_size=None, **kwargs):
    """Send data in bulk to Elasticsearch."""
    return es_bulk(get_client(), actions=actions, chunk_size=chunk_size, **kwargs)

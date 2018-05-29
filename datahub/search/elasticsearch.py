from logging import getLogger
from urllib.parse import urlparse

from aws_requests_auth.aws_auth import AWSRequestsAuth
from django.conf import settings
from django_pglocks import advisory_lock
from elasticsearch import RequestsHttpConnection
from elasticsearch.helpers import bulk as es_bulk
from elasticsearch_dsl import analysis, Index
from elasticsearch_dsl.connections import connections

from datahub.search.apps import get_search_apps


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


def index_exists(name=settings.ES_INDEX):
    """
    :param name: Name of the index

    :returns: True if index_name exists
    """
    return get_client().indices.exists(index=name)


def configure_index(index_name, index_settings=None):
    """Configures Elasticsearch index."""
    if not index_exists(name=index_name):
        index = Index(index_name)
        for analyzer in ANALYZERS:
            index.analyzer(analyzer)

        if index_settings:
            index.settings(**index_settings)
        index.create()


def init_es():
    """Creates the Elasticsearch index if it doesn't exist, and updates the mapping."""
    logger.info('Creating Elasticsearch index and initialising mapping...')

    with advisory_lock('leeloo_init_es'):
        configure_index(settings.ES_INDEX, index_settings=settings.ES_INDEX_SETTINGS)

        for search_app in get_search_apps():
            search_app.init_es()

    logger.info('Elasticsearch index and mapping initialised')


def bulk(actions=None, chunk_size=None, **kwargs):
    """Send data in bulk to Elasticsearch."""
    return es_bulk(get_client(), actions=actions, chunk_size=chunk_size, **kwargs)

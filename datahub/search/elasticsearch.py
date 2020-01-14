from contextlib import contextmanager
from logging import getLogger

from django.conf import settings
from elasticsearch.helpers import bulk as es_bulk
from elasticsearch_dsl import analysis, Index
from elasticsearch_dsl.connections import connections


logger = getLogger(__name__)


# Normalises values to improve sorting (by keeping e, E, è, ê etc. together)
lowercase_asciifolding_normalizer = analysis.normalizer(
    'lowercase_asciifolding_normalizer',
    filter=('lowercase', 'asciifolding'),
)

# Trigram tokenizer enables us to support partial matching
trigram = analysis.tokenizer(
    'trigram',
    'nGram',
    min_gram=3,
    max_gram=3,
    token_chars=('letter', 'digit'),
)

# Filters out "-" so that t-shirt and tshirt can be matched
special_chars = analysis.char_filter('special_chars', 'mapping', mappings=('-=>',))
trigram_analyzer = analysis.CustomAnalyzer(
    'trigram_analyzer',
    tokenizer=trigram,
    char_filter=special_chars,
    filter=('lowercase',),
)

space_remover = analysis.token_filter(
    'space_remover',
    type='pattern_replace',
    pattern=' ',
    replacement='',
)

AREA_REGEX = r'[a-z]{1,2}'
DISTRICT_REGEX = r'[0-9][a-z]|[0-9]{1,2}'
SECTOR_REGEX = r'[0-9]'
UNIT_REGEX = r'[a-z]{2}'

postcode_filter = analysis.token_filter(
    'postcode_filter',
    type='pattern_capture',
    # Match whole postcode
    preserve_original=True,
    patterns=[
        # Match postcode area
        # See the Royal Mail programmer's guide for the exact definitions
        rf'^({AREA_REGEX})(?:{DISTRICT_REGEX}){SECTOR_REGEX}{UNIT_REGEX}',

        # Match postcode district (with sub-district code ignored)
        # This is so `wc1` query would match `wc1ab` and `wc1a1ab`, but not `wc111ab`
        # Area + one or two digits
        rf'^(({AREA_REGEX}[0-9]){SECTOR_REGEX}{UNIT_REGEX}|'
        rf'({AREA_REGEX}[0-9]{{2}}){SECTOR_REGEX}{UNIT_REGEX}|'
        rf'({AREA_REGEX}[0-9])[a-z]?{SECTOR_REGEX}{UNIT_REGEX})',

        # Match postcode district (including sub-district)
        rf'^({AREA_REGEX}(?:{DISTRICT_REGEX})){SECTOR_REGEX}{UNIT_REGEX}',

        # Match postcode sector
        rf'^({AREA_REGEX}(?:{DISTRICT_REGEX}){SECTOR_REGEX}){UNIT_REGEX}',
    ],
)


postcode_analyzer = analysis.CustomAnalyzer(
    'postcode_analyzer',
    type='custom',
    tokenizer='keyword',
    filter=(space_remover, 'lowercase', postcode_filter),
)


postcode_search_analyzer = analysis.CustomAnalyzer(
    'postcode_search_analyzer',
    type='custom',
    tokenizer='keyword',
    filter=(space_remover, 'lowercase'),
)


english_possessive_stemmer = analysis.token_filter(
    'english_possessive_stemmer',
    type='stemmer',
    language='possessive_english',
)

english_stemmer = analysis.token_filter(
    'english_stemmer',
    type='stemmer',
    language='english',
)

english_stop = analysis.token_filter(
    'english_stop',
    type='stop',
    stopwords='_english_',
)

english_analyzer = analysis.CustomAnalyzer(
    'english_analyzer',
    tokenizer='standard',
    filter=[
        english_possessive_stemmer,
        'lowercase',
        english_stop,
        english_stemmer,
    ],
)


ANALYZERS = (
    trigram_analyzer,
    english_analyzer,
)


def configure_connection():
    """Configure Elasticsearch default connection."""
    connections_default = {
        'hosts': [settings.ES_URL],
        'verify_certs': settings.ES_VERIFY_CERTS,
    }
    connections.configure(default=connections_default)


def get_client():
    """Gets an instance of the Elasticsearch client from the connection cache."""
    return connections.get_connection()


def index_exists(index_name):
    """Checks if an index exists."""
    client = get_client()
    return client.indices.exists(index_name)


def create_index(index_name, mapping, alias_names=()):
    """
    Creates an index, initialises it with a mapping, and optionally associates aliases with it.

    Note: If you need to perform multiple alias operations atomically, you should use
    start_alias_transaction() instead of specifying aliases when creating an index.
    """
    index = Index(index_name, mapping.doc_type)
    for analyzer in ANALYZERS:
        index.analyzer(analyzer)

    index.settings(**settings.ES_INDEX_SETTINGS)
    index.mapping(mapping)

    # ES allows you to specify filter criteria for aliases but we don't make use of that –
    # hence the empty dict for each alias
    alias_mapping = {alias_name: {} for alias_name in alias_names}
    index.aliases(**alias_mapping)

    index.create()


def delete_index(index_name):
    """Deletes an index."""
    logger.info(f'Deleting the {index_name} index...')
    client = get_client()
    client.indices.delete(index_name)


def get_indices_for_aliases(*alias_names):
    """Gets the indices referenced by one or more aliases."""
    client = get_client()
    alias_to_index_mapping = {alias_name: set() for alias_name in alias_names}
    index_to_alias_mapping = client.indices.get_alias(name=alias_names)

    for index_name, index_properties in index_to_alias_mapping.items():
        for alias_name in index_properties['aliases']:
            alias_to_index_mapping[alias_name].add(index_name)

    return [alias_to_index_mapping[alias_name] for alias_name in alias_names]


def get_aliases_for_index(index_name):
    """Gets the aliases referencing an index."""
    client = get_client()
    alias_response = client.indices.get_alias(index=index_name)
    return alias_response[index_name]['aliases'].keys()


def alias_exists(alias_name):
    """Checks if an alias exists."""
    client = get_client()
    return client.indices.exists_alias(name=alias_name)


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

    def associate_indices_with_alias(self, alias_name, index_names):
        """Adds a pending operation to associate a new or existing alias with a set of indices."""
        self.actions.append({
            'add': {
                'alias': alias_name,
                'indices': list(index_names),
            },
        })

    def dissociate_indices_from_alias(self, alias_name, index_names):
        """Adds a pending operation to dissociate an existing alias from a set of indices."""
        self.actions.append({
            'remove': {
                'alias': alias_name,
                'indices': list(index_names),
            },
        })

    def commit(self):
        """Commits (flushes) pending operations."""
        client = get_client()
        client.indices.update_aliases(body={
            'actions': self.actions,
        })
        self.actions = []


@contextmanager
def start_alias_transaction():
    """
    Returns a context manager that can be used to create and update aliases atomically.

    Changes are committed when the context manager exits.

    Usage example:
        with start_alias_transaction() as alias_transaction:
            alias_transaction.dissociate_indices_from_alias(
                'some-alias',
                ['an-index', 'another-index],
            )
            alias_transaction.associate_indices_with_alias(
                'another-alias',
                ['new-index],
            )
    """
    alias_updater = _AliasUpdater()
    yield alias_updater
    alias_updater.commit()


def associate_index_with_alias(alias_name, index_name):
    """
    Associates a new or existing alias with an index.

    This is only intended to be a convenience function for simple operations. For more complex
    operations, use start_alias_transaction().
    """
    client = get_client()
    client.indices.put_alias(index_name, alias_name)


def bulk(
    actions=None,
    chunk_size=500,
    max_chunk_bytes=settings.ES_BULK_MAX_CHUNK_BYTES,
    **kwargs,
):
    """Send data in bulk to Elasticsearch."""
    return es_bulk(
        get_client(),
        actions=actions,
        chunk_size=chunk_size,
        max_chunk_bytes=max_chunk_bytes,
        **kwargs,
    )

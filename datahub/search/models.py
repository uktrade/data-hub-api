from hashlib import blake2b
from logging import getLogger

from django.conf import settings
from elasticsearch_dsl import DocType, MetaField

from datahub.core.exceptions import DataHubException
from datahub.search.elasticsearch import (
    alias_exists,
    associate_alias_with_index,
    create_index,
    get_indices_for_alias,
    get_indices_for_aliases,
    index_exists,
)
from datahub.search.utils import get_model_non_mapped_field_names, serialise_mapping


logger = getLogger(__name__)


class BaseESModel(DocType):
    """Helps convert Django models to dictionaries."""

    MAPPINGS = {}

    COMPUTED_MAPPINGS = {}

    SEARCH_FIELDS = ()

    # Fields that have been renamed in some way, and were used as part of a filter.
    # While an index migration is in progress, a composite filter must be used so that the
    # filter works with both the old and new index.
    # Such fields should be listed in this attribute it make it clear why they're being referenced.
    # Once the migration is complete in all environments, the composite filter can be updated
    # and the field removed from here.
    PREVIOUS_MAPPING_FIELDS = ()

    class Meta:
        dynamic = MetaField('false')

    @classmethod
    def get_read_alias(cls):
        """Gets the alias to be used for read operations."""
        return f'{settings.ES_INDEX_PREFIX}-{cls._doc_type.name}-read'

    @classmethod
    def get_write_alias(cls):
        """Gets the alias to be used for write operations."""
        return f'{settings.ES_INDEX_PREFIX}-{cls._doc_type.name}-write'

    @classmethod
    def get_write_index(cls):
        """Gets the index currently referenced by the write alias."""
        indices = get_indices_for_alias(cls.get_write_alias())
        return _get_write_index(indices)

    @classmethod
    def get_read_and_write_indices(cls):
        """Gets the indices currently referenced by the read and write aliases."""
        read_indices, write_indices = get_indices_for_aliases(
            cls.get_read_alias(), cls.get_write_alias()
        )
        return read_indices, _get_write_index(write_indices)

    @classmethod
    def get_index_prefix(cls):
        """Gets the prefix used for indices and aliases."""
        return f'{settings.ES_INDEX_PREFIX}-{cls._doc_type.name}-'

    @classmethod
    def get_target_mapping_hash(cls):
        """Gets a unique hash digest for mapping (as defined in the code base)."""
        mapping_data = serialise_mapping(cls._doc_type.mapping.to_dict())
        return blake2b(mapping_data, digest_size=16).hexdigest()

    @classmethod
    def get_current_mapping_hash(cls):
        """Extracts and returns the mapping hash from the current index name."""
        current_write_index = cls.get_write_index()
        prefix = cls.get_index_prefix()
        if not current_write_index.startswith(prefix):
            logger.warning(f'Unexpected index prefix for search model {cls._doc_type.name} and '
                           f'index {current_write_index}. It may be a legacy index.')
            return ''
        return current_write_index[len(prefix):]

    @classmethod
    def get_target_index_name(cls):
        """Generates a unique name for the index based on its mapping."""
        mapping_hash = cls.get_target_mapping_hash()
        prefix = cls.get_index_prefix()
        return f'{prefix}{mapping_hash}'

    @classmethod
    def is_migration_needed(cls):
        """Returns whether the active mapping is out of date and a migration is needed."""
        target_mapping_hash = cls.get_target_mapping_hash()
        return cls.get_current_mapping_hash() != target_mapping_hash

    @classmethod
    def was_migration_started(cls):
        """
        Returns whether a migration was started and has not completed.

        This could be a a migration still in progress, or an aborted migration.
        """
        read_indices, _ = cls.get_read_and_write_indices()
        return len(read_indices) != 1

    @classmethod
    def initialise_index(cls, force_update_mapping=False):
        """
        Creates the index and aliases for this model if they don't already exist.

        If force_update_mapping is True and the write alias already exists, an attempt
        is made to update to update the existing mapping in place.
        """
        read_alias_exists = alias_exists(cls.get_read_alias())
        write_alias_exists = alias_exists(cls.get_write_alias())
        if not write_alias_exists:
            # Handle migration from the legacy single-index set-up
            # TODO: Remove once all environments have been migrated to the new structure
            if settings.ES_LEGACY_INDEX and index_exists(settings.ES_LEGACY_INDEX):
                index_name = settings.ES_LEGACY_INDEX
            else:
                index_name = cls.get_target_index_name()
                cls.create_index(index_name)

            associate_alias_with_index(cls.get_write_alias(), index_name)
        elif force_update_mapping:
            cls.init(cls.get_write_alias())

        if not read_alias_exists:
            associate_alias_with_index(cls.get_read_alias(), cls.get_write_index())

    @classmethod
    def create_index(cls, index_name):
        """Creates an index with this model's mapping."""
        create_index(index_name, index_settings=settings.ES_INDEX_SETTINGS)
        cls.init(index_name)

    @classmethod
    def es_document(cls, dbmodel, index=None):
        """Creates Elasticsearch document."""
        source = cls.db_object_to_dict(dbmodel)

        return {
            '_index': index or cls.get_write_alias(),
            '_type': cls._doc_type.name,
            '_id': source.get('id'),
            '_source': source,
        }

    @classmethod
    def db_object_to_dict(cls, dbmodel):
        """Converts a DB model object to a dictionary suitable for Elasticsearch."""
        mapped_values = (
            (col, fn, getattr(dbmodel, col)) for col, fn in cls.MAPPINGS.items()
        )
        fields = get_model_non_mapped_field_names(cls)

        result = {
            **{col: fn(val) if val is not None else None for col, fn, val in mapped_values},
            **{col: fn(dbmodel) for col, fn in cls.COMPUTED_MAPPINGS.items()},
            **{field: getattr(dbmodel, field) for field in fields},
        }

        return result

    @classmethod
    def db_objects_to_es_documents(cls, dbmodels, index=None):
        """Converts DB model objects to Elasticsearch documents."""
        for dbmodel in dbmodels:
            yield cls.es_document(dbmodel, index=index)


def _get_write_index(indices):
    if len(indices) != 1:
        raise DataHubException(
            'Unexpected alias state; write alias references multiple indices',
        )
    return next(iter(indices))

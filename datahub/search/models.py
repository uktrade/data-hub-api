from hashlib import blake2b
from logging import getLogger

from django.conf import settings
from elasticsearch_dsl import Document, Keyword, MetaField

from datahub.core.exceptions import DataHubException
from datahub.search.apps import get_search_app_by_search_model
from datahub.search.elasticsearch import (
    alias_exists,
    associate_index_with_alias,
    create_index,
    get_indices_for_aliases,
)
from datahub.search.utils import get_model_non_mapped_field_names, serialise_mapping


logger = getLogger(__name__)


class BaseESModel(Document):
    """Helps convert Django models to dictionaries."""

    # This is a replacement for the _type (mapping type name) field which is deprecated in
    # Elasticsearch.
    # It’s required for the aggregations used in global search.
    _document_type = Keyword()

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
    def get_app_name(cls):
        """Get the search app name for this search model."""
        return get_search_app_by_search_model(cls).name

    @classmethod
    def get_read_alias(cls):
        """Gets the alias to be used for read operations."""
        return f'{settings.ES_INDEX_PREFIX}-{cls.get_app_name()}-read'

    @classmethod
    def get_write_alias(cls):
        """Gets the alias to be used for write operations."""
        return f'{settings.ES_INDEX_PREFIX}-{cls.get_app_name()}-write'

    @classmethod
    def get_write_index(cls):
        """Gets the index currently referenced by the write alias."""
        indices, = get_indices_for_aliases(cls.get_write_alias())
        return _get_write_index(indices)

    @classmethod
    def get_read_and_write_indices(cls):
        """Gets the indices currently referenced by the read and write aliases."""
        read_indices, write_indices = get_indices_for_aliases(
            cls.get_read_alias(), cls.get_write_alias(),
        )
        return read_indices, _get_write_index(write_indices)

    @classmethod
    def get_index_prefix(cls):
        """Gets the prefix used for indices and aliases."""
        return f'{settings.ES_INDEX_PREFIX}-{cls.get_app_name()}-'

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
            logger.warning(
                f'Unexpected index prefix for search model {cls.get_app_name()} and '
                f'index {current_write_index}. It may be a legacy index.',
            )
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
    def set_up_index_and_aliases(cls):
        """Creates the index and aliases for this model if they don't already exist."""
        if not alias_exists(cls.get_write_alias()):
            index_name = cls.get_target_index_name()
            alias_names = (cls.get_write_alias(), cls.get_read_alias())
            create_index(index_name, cls._doc_type.mapping, alias_names=alias_names)
            return True

        # Should not normally happen
        if not alias_exists(cls.get_read_alias()):
            logger.warning(
                f'Missing read alias {cls.get_read_alias()} detected, recreating the alias...',
            )
            associate_index_with_alias(cls.get_read_alias(), cls.get_write_index())

        return False

    @classmethod
    def es_document(cls, db_object, index=None, include_index=True, include_source=True):
        """
        Creates a dict representation an Elasticsearch document.

        include_index and include_source can be set to False when the _index and/or _source keys
        aren't required (e.g. when using `datahub.search.deletion.delete_documents()`).
        """
        doc = {
            '_type': cls._doc_type.name,
            '_id': db_object.pk,
        }

        if include_index:
            doc['_index'] = index or cls.get_write_alias()

        if include_source:
            doc['_source'] = cls.db_object_to_dict(db_object)

        return doc

    @classmethod
    def db_object_to_dict(cls, db_object):
        """Converts a DB model object to a dictionary suitable for Elasticsearch."""
        mapped_values = (
            (col, fn, getattr(db_object, col)) for col, fn in cls.MAPPINGS.items()
        )
        fields = get_model_non_mapped_field_names(cls)

        result = {
            **{col: fn(val) if val is not None else None for col, fn, val in mapped_values},
            **{col: fn(db_object) for col, fn in cls.COMPUTED_MAPPINGS.items()},
            **{field: getattr(db_object, field) for field in fields},
            '_document_type': cls.get_app_name(),
        }

        return result

    @classmethod
    def db_objects_to_es_documents(cls, db_objects, index=None):
        """Converts DB model objects to Elasticsearch documents."""
        for db_object in db_objects:
            yield cls.es_document(db_object, index=index)


def _get_write_index(indices):
    if len(indices) != 1:
        raise DataHubException(
            'Unexpected alias state; write alias references multiple indices',
        )
    return next(iter(indices))

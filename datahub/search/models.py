from django.conf import settings
from elasticsearch_dsl import DocType, MetaField

from datahub.search.utils import get_model_non_mapped_field_names


class BaseESModel(DocType):
    """Helps convert Django models to dictionaries."""

    MAPPINGS = {}

    COMPUTED_MAPPINGS = {}

    SEARCH_FIELDS = ()

    class Meta:
        dynamic = MetaField('false')

    @classmethod
    def es_document(cls, dbmodel):
        """Creates Elasticsearch document."""
        source = cls.db_object_to_dict(dbmodel)

        # TODO could get index and doc type from meta of other class
        return {
            '_index': settings.ES_INDEX,
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
    def db_objects_to_es_documents(cls, dbmodels):
        """Converts DB model objects to Elasticsearch documents."""
        for dbmodel in dbmodels:
            yield cls.es_document(dbmodel)

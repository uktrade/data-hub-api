from collections import namedtuple

from django.conf import settings

from datahub.search.utils import get_model_non_mapped_field_names

DataSet = namedtuple('DataSet', ('queryset', 'es_model',))


class MapDBModelToDict:
    """Helps convert Django models to dictionaries."""

    MAPPINGS = {}

    COMPUTED_MAPPINGS = {}

    SEARCH_FIELDS = ()

    @classmethod
    def es_document(cls, dbmodel):
        """Creates Elasticsearch document."""
        source = cls.dbmodel_to_dict(dbmodel)

        # TODO could get index and doc type from meta of other class
        return {
            '_index': settings.ES_INDEX,
            '_type': cls._doc_type.name,
            '_id': source.get('id'),
            '_source': source,
        }

    @classmethod
    def dbmodel_to_dict(cls, dbmodel):
        """Converts dbmodel instance to a dictionary suitable for ElasticSearch."""
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
    def dbmodels_to_es_documents(cls, dbmodels):
        """Converts db models to Elasticsearch documents."""
        for dbmodel in dbmodels:
            yield cls.es_document(dbmodel)

from collections import namedtuple

from django.conf import settings

DataSet = namedtuple('DataSet', ('queryset', 'es_model',))


class MapDBModelToDict:
    """Helps convert Django models to dictionaries."""

    IGNORED_FIELDS = ()

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
        result = {col: fn(getattr(dbmodel, col)) for col, fn in cls.MAPPINGS.items()
                  if getattr(dbmodel, col) is not None}

        result.update({
            col: fn(dbmodel) for col, fn in cls.COMPUTED_MAPPINGS.items()
        })

        fields = [field for field in dbmodel._meta.get_fields()
                  if field.name not in cls.IGNORED_FIELDS]

        obj = {f.name: getattr(dbmodel, f.name) for f in fields if f.name not in result}
        result.update(obj.items())

        return result

    @classmethod
    def dbmodels_to_es_documents(cls, dbmodels):
        """Converts db models to Elasticsearch documents."""
        for dbmodel in dbmodels:
            yield cls.es_document(dbmodel)

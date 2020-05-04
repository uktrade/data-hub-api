from elasticsearch_dsl import Date, Keyword, Text

from datahub.search import fields
from datahub.search.models import BaseESModel, DEFAULT_MAPPING_TYPE


class ESSimpleModel(BaseESModel):
    """Elasticsearch representation of SimpleModel model."""

    id = Keyword()
    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    date = Date()

    SEARCH_FIELDS = (
        'name',
        'name.trigram',
    )

    class Index:
        doc_type = DEFAULT_MAPPING_TYPE

    class Meta:
        """Default document meta data."""

        doc_type = DEFAULT_MAPPING_TYPE

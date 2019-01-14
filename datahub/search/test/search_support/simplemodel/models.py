from elasticsearch_dsl import Keyword, Text

from datahub.search import fields
from datahub.search.models import BaseESModel


DOC_TYPE = 'simplemodel'


class ESSimpleModel(BaseESModel):
    """Elasticsearch representation of SimpleModel model."""

    id = Keyword()
    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )

    SEARCH_FIELDS = (
        'name',
        'name.trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE

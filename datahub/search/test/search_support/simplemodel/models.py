from opensearch_dsl import Date, Keyword, Text

from datahub.search import fields
from datahub.search.models import BaseSearchModel


class SearchSimpleModel(BaseSearchModel):
    """OpenSearch representation of SimpleModel model."""

    id = Keyword()
    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    country = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    address = Text(
        fields={
            'trigram': fields.TrigramText(),
        },
    )
    date = Date()

    SEARCH_FIELDS = (
        'name',
        'name.trigram',
        'country.trigram',
        'address.trigram',
    )

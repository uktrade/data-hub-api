from elasticsearch_dsl import Keyword

from .... import fields
from ....models import BaseESModel


class ESSimpleModel(BaseESModel):
    """Elasticsearch representation of SimpleModel model."""

    id = Keyword()
    name = fields.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = fields.SortableCaseInsensitiveKeywordText()
    name_trigram = fields.TrigramText()

    MAPPINGS = {
        'id': str,
    }

    SEARCH_FIELDS = (
        'name',
        'name_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = 'simplemodel'

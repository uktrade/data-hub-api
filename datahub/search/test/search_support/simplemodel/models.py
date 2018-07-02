from elasticsearch_dsl import Keyword

from .... import dsl_utils
from ....models import BaseESModel


class ESSimpleModel(BaseESModel):
    """Elasticsearch representation of SimpleModel model."""

    id = Keyword()
    name = dsl_utils.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.TrigramText()

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

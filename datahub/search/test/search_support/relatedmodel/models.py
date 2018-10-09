from elasticsearch_dsl import Keyword

from datahub.search import dict_utils
from datahub.search import fields
from datahub.search.models import BaseESModel


DOC_TYPE = 'relatedmodel'


class ESRelatedModel(BaseESModel):
    """Elasticsearch representation of SimpleModel model."""

    id = Keyword()
    simpleton = fields.nested_id_name_field()

    MAPPINGS = {
        'id': dict_utils.id_name_dict,
    }

    SEARCH_FIELDS = ()

    class Meta:
        """Model configuration."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE

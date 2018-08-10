from elasticsearch_dsl import Keyword

from .... import dict_utils, fields
from ....models import BaseESModel


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

        doc_type = 'relatedmodel'

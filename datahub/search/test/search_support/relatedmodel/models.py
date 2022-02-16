from opensearch_dsl import Keyword

from datahub.search import dict_utils
from datahub.search import fields
from datahub.search.models import BaseSearchModel


class SearchRelatedModel(BaseSearchModel):
    """OpenSearch representation of SimpleModel model."""

    id = Keyword()
    simpleton = fields.id_name_field()

    MAPPINGS = {
        'simpleton': dict_utils.id_name_dict,
    }

    SEARCH_FIELDS = ('simpleton.name',)

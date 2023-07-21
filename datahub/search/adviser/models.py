from opensearch_dsl import Boolean, Keyword, Text


from datahub.search import dict_utils, fields
from datahub.search.models import BaseSearchModel


class Adviser(BaseSearchModel):
    """Adviser model"""

    id = Keyword()
    first_name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    last_name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    name = Text()
    dit_team = fields.id_name_field()
    is_active = Boolean()

    MAPPINGS = {
        'dit_team': dict_utils.id_name_dict,
    }

    SEARCH_FIELDS = (
        'id',
        'first_name',  # to find 2-letter words
        'first_name.trigram',
        'last_name',  # to find 2-letter words
        'last_name.trigram',
        'is_active',
        'name',
    )

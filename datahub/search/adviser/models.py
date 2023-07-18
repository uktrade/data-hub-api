from functools import partial

from opensearch_dsl import Boolean, Date, Integer, Keyword, Object, Text

from datahub.company.models import CompanyExportCountry
from datahub.search import dict_utils, fields
from datahub.search.models import BaseSearchModel


class Adviser(BaseSearchModel):
    """Empty model"""

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

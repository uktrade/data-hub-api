from django.db.models.expressions import Case, Value, When
from django.db.models.fields import CharField
from django.db.models.functions import Cast, Concat, Upper


from rest_framework.views import APIView
from rest_framework.response import Response

from config.settings.types import HawkScope
from datahub.company.models import Advisor as DBAdvisor, CompanyPermission
from datahub.company.models import Company as DBCompany, CompanyExportCountry
from datahub.core.auth import PaaSIPAuthentication
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.query_utils import (
    get_front_end_url_expression,
    get_string_agg_subquery,
)
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.search.adviser import AdviserSearchApp
from datahub.search.adviser.serializers import (
    SearchAdviserQuerySerializer,
)
from datahub.search.views import (
    register_v4_view,
    SearchAPIView,
)


class SearchAdviserAPIViewMixin:
    """Defines common settings."""

    search_app = AdviserSearchApp
    serializer_class = SearchAdviserQuerySerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }
    fields_to_exclude = ()

    FILTER_FIELDS = (
        'id',
        'first_name',
        'last_name',
    )

    REMAP_FIELDS = {}

    COMPOSITE_FILTERS = {
        'name': [
            'name',  # to find 2-letter words
            'name.trigram',
            'trading_names',  # to find 2-letter words
            'trading_names.trigram',
        ],
    }


@register_v4_view()
class SearchAdviserAPIView(SearchAdviserAPIViewMixin, SearchAPIView):
    pass

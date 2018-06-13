from datahub.oauth.scopes import Scope
from .models import Order
from .serializers import SearchOrderSerializer
from ..views import SearchAPIView


class SearchOrderParams:
    """Search order params."""

    required_scopes = (Scope.internal_front_end,)
    entity = Order
    serializer_class = SearchOrderSerializer

    FILTER_FIELDS = [
        'primary_market',
        'sector_descends',
        'uk_region',
        'created_on_before',
        'created_on_after',
        'assigned_to_adviser',
        'assigned_to_team',
        'status',
        'reference',
        'total_cost',
        'subtotal_cost',
        'contact_name',
        'company_name',
        'company',
    ]

    REMAP_FIELDS = {
        'primary_market': 'primary_market.id',
        'uk_region': 'uk_region.id',
        'assigned_to_adviser': 'assignees.id',
        'assigned_to_team': 'assignees.dit_team.id',
        'company': 'company.id',
        'reference': 'reference_trigram',
    }

    COMPOSITE_FILTERS = {
        'contact_name': [
            'contact.name',
            'contact.name_trigram'
        ],
        'company_name': [
            'company.name',
            'company.name_trigram',
            'company.trading_name',
            'company.trading_name_trigram',
        ],
        'sector_descends': [
            'sector.id',
            'sector.ancestors.id',
        ],
    }


class SearchOrderAPIView(SearchOrderParams, SearchAPIView):
    """Filtered order search view."""

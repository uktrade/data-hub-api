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
        'created_on_before',
        'created_on_after',
        'assigned_to_adviser',
        'assigned_to_team',
    ]

    REMAP_FIELDS = {
        'primary_market': 'primary_market.id',
        'assigned_to_adviser': 'assignees.id',
        'assigned_to_team': 'assignees.dit_team.id',
    }


class SearchOrderAPIView(SearchOrderParams, SearchAPIView):
    """Filtered order search view."""

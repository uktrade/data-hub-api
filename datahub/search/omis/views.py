from rest_framework.views import APIView

from .models import Order
from ..views import SearchWithFiltersAPIMixin


class SearchOrderAPIView(SearchWithFiltersAPIMixin, APIView):
    """Filtered order search view."""

    entity = Order

    DEFAULT_ORDERING = 'created_on:desc'

    SORT_BY_FIELDS = ['created_on']

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

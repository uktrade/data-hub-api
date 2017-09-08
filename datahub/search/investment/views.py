from .models import InvestmentProject
from .serializers import SearchInvestmentProjectSerializer
from ..views import SearchAPIView


class SearchInvestmentProjectAPIView(SearchAPIView):
    """Filtered investment project search view."""

    entity = InvestmentProject
    serializer_class = SearchInvestmentProjectSerializer

    include_aggregations = True

    FILTER_FIELDS = (
        'client_relationship_manager',
        'estimated_land_date_after',
        'estimated_land_date_before',
        'investment_type',
        'investor_company',
        'sector',
        'stage'
    )

    REMAP_FIELDS = {
        'client_relationship_manager': 'client_relationship_manager.id',
        'investment_type': 'investment_type.id',
        'investor_company': 'investor_company.id',
        'sector': 'sector.id',
        'stage': 'stage.id',
    }

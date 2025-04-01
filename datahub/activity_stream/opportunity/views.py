from datahub.activity_stream.opportunity.serializers import (
    LargeCapitalOpportunityActivitySerializer,
)
from datahub.activity_stream.pagination import ActivityCursorPagination
from datahub.activity_stream.views import ActivityViewSet
from datahub.investment.opportunity.models import LargeCapitalOpportunity


class LargeCapitalOpportunityPagination(ActivityCursorPagination):
    """Cursor pagination for Large Capital Opportunity."""

    summary = 'Large Capital Opportunity Activities Added'


class LargeCapitalOpportunityActivityViewSet(ActivityViewSet):
    """Large Capital Opportunity ViewSet for the activity stream."""

    pagination_class = LargeCapitalOpportunityPagination
    serializer_class = LargeCapitalOpportunityActivitySerializer
    queryset = LargeCapitalOpportunity.objects.all()

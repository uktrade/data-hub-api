from datahub.activity_stream.investor_profile.serializers import (
    LargeCapitalInvestorProfileActivitySerializer,
)
from datahub.activity_stream.pagination import ActivityCursorPagination
from datahub.activity_stream.views import ActivityViewSet
from datahub.investment.investor_profile.models import LargeCapitalInvestorProfile


class LargeCapitalInvestorProfileCursorPagination(ActivityCursorPagination):
    """
    Cursor pagination for Large Capital Investor Profile.

    `modified_on` is mutable. Most recently updated company referrals would be consumed first,
    so they get a chance to appear in the Activity Feed quicker.
    """

    ordering = ('modified_on', 'pk')
    summary = 'Large Capital Investor Profile Activities'


class LargeCapitalInvestorProfileActivityViewSet(ActivityViewSet):
    """
    Large Capital Investor Profile ViewSet for the activity stream
    """

    pagination_class = LargeCapitalInvestorProfileCursorPagination
    serializer_class = LargeCapitalInvestorProfileActivitySerializer
    queryset = LargeCapitalInvestorProfile.objects.select_related(
        'created_by',
        'modified_by',
        'investor_company',
        'investor_type',
        'required_checks_conducted',
        'required_checks_conducted_by',
        'minimum_return_rate',
        'minimum_equity_percentage',
    )

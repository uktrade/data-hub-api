from datahub.activity_stream.company_referral.serializers import CompanyReferralActivitySerializer
from datahub.activity_stream.pagination import ActivityCursorPagination
from datahub.activity_stream.views import ActivityViewSet
from datahub.company_referral.models import CompanyReferral


class CompanyReferralCursorPagination(ActivityCursorPagination):
    """
    Cursor pagination for Company Referral.

    `modified_on` is mutable. Most recently updated company referrals would be consumed first,
    so they get a chance to appear in the Activity Feed quicker.
    """

    ordering = ('modified_on', 'pk')
    summary = 'Company Referral Activities'


class CompanyReferralActivityViewSet(ActivityViewSet):
    """
    Interaction ViewSet for the activity stream
    """

    pagination_class = CompanyReferralCursorPagination
    serializer_class = CompanyReferralActivitySerializer
    queryset = CompanyReferral.objects.select_related(
        'company',
        'contact',
        'created_by__dit_team',
        'closed_by__dit_team',
        'completed_by__dit_team',
        'recipient__dit_team',
    )

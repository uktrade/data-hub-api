from rest_framework.generics import RetrieveAPIView

from datahub.company.models import Advisor
from datahub.investment.summary.schemas import IProjectSummarySchema
from datahub.investment.summary.serializers import AdvisorIProjectSummarySerializer


class IProjectSummaryView(RetrieveAPIView):
    """
    Summary of Investment Projects for an adviser.

    Shows the counts for each stage for the current and previous financial years.
    """

    schema = IProjectSummarySchema()
    serializer_class = AdvisorIProjectSummarySerializer
    lookup_url_kwarg = 'adviser_pk'
    queryset = Advisor.objects.all()

from django.db.models import Prefetch

from datahub.activity_stream.investment.serializers import IProjectCreatedSerializer
from datahub.activity_stream.pagination import ActivityCursorPagination
from datahub.activity_stream.views import ActivityViewSet
from datahub.company.models import Contact
from datahub.investment.project.models import InvestmentProject


class IProjectCreatedPagination(ActivityCursorPagination):
    """
    Investment Project added CursorPagination for activity stream.
    """

    ordering = ('created_on', 'pk')
    summary = 'Investment Activities Added'


class IProjectCreatedViewSet(ActivityViewSet):
    """
    Investment Project added ViewSet for activity stream
    """

    pagination_class = IProjectCreatedPagination
    serializer_class = IProjectCreatedSerializer
    queryset = InvestmentProject.objects.select_related(
        'created_by',
        'investment_type',
        'investor_company',
        'investment_type',
        'stage',
    ).prefetch_related(
        Prefetch('client_contacts', queryset=Contact.objects.order_by('pk')),
    )

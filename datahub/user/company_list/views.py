from rest_framework.filters import OrderingFilter

from datahub.core.viewsets import CoreViewSet
from datahub.oauth.scopes import Scope
from datahub.user.company_list.models import CompanyList
from datahub.user.company_list.serializers import CompanyListSerializer


class CompanyListViewSet(CoreViewSet):
    """
    Views for managing the authenticated user's company lists.

    Currently, this covers listing lists only.
    """

    required_scopes = (Scope.internal_front_end,)
    queryset = CompanyList.objects.all()
    serializer_class = CompanyListSerializer
    filter_backends = (OrderingFilter,)
    ordering = ('name', 'created_on', 'pk')

    def get_queryset(self):
        """Get a query set filtered to the authenticated user's lists."""
        return super().get_queryset().filter(adviser=self.request.user)

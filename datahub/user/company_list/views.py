from rest_framework.filters import OrderingFilter

from datahub.core.viewsets import CoreViewSet
from datahub.oauth.scopes import Scope
from datahub.user.company_list.models import CompanyList
from datahub.user.company_list.serializers import CompanyListSerializer


class CompanyListViewSet(CoreViewSet):
    """
    Views for managing the authenticated user's company lists.

    This covers creating and listing lists.
    """

    required_scopes = (Scope.internal_front_end,)
    queryset = CompanyList.objects.all()
    serializer_class = CompanyListSerializer
    filter_backends = (OrderingFilter,)
    ordering = ('name', 'created_on', 'pk')

    def get_queryset(self):
        """Get a query set filtered to the authenticated user's lists."""
        return super().get_queryset().filter(adviser=self.request.user)

    def get_additional_data(self, create):
        """
        Set additional data for when serializer.save() is called.

        This makes sure that adviser is set to self.request.user when a list is created
        (in the same way created_by and modified_by are).

        TODO: When we have support for updating (i.e. renaming) lists, change this to not overwrite
         adviser when create=False.
        """
        additional_data = super().get_additional_data(create)

        return {
            **additional_data,
            'adviser': self.request.user,
        }

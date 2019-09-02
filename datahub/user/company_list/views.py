from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import DestroyModelMixin

from datahub.core.query_utils import get_aggregate_subquery
from datahub.core.viewsets import CoreViewSet
from datahub.oauth.scopes import Scope
from datahub.user.company_list.models import CompanyList
from datahub.user.company_list.serializers import CompanyListSerializer


class CompanyListViewSet(CoreViewSet, DestroyModelMixin):
    """
    Views for managing the authenticated user's company lists.

    This covers creating, updating (i.e. renaming), deleting and listing lists.
    """

    required_scopes = (Scope.internal_front_end,)
    queryset = CompanyList.objects.annotate(
        item_count=get_aggregate_subquery(CompanyList, Count('items')),
    )
    serializer_class = CompanyListSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ('items__company_id',)
    ordering = ('name', 'created_on', 'pk')

    def get_queryset(self):
        """Get a query set filtered to the authenticated user's lists."""
        return super().get_queryset().filter(adviser=self.request.user)

    def get_additional_data(self, create):
        """
        Set additional data for when serializer.save() is called.

        This makes sure that adviser is set to self.request.user when a list is created
        (in the same way created_by and modified_by are).
        """
        additional_data = super().get_additional_data(create)

        if not create:
            # A list is being updated rather than created, so leave the adviser field unchanged
            # (as there is no reason to change it)
            return additional_data

        return {
            **additional_data,
            'adviser': self.request.user,
        }

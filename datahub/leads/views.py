"""Business lead views."""

from django_filters.rest_framework import DjangoFilterBackend

from datahub.core.viewsets import CoreViewSetV3
from datahub.leads.models import BusinessLead
from datahub.leads.serializers import BusinessLeadSerializer


class BusinessLeadViewSet(CoreViewSetV3):
    """
    Business lead views.

    Users can only view business leads that are associated with them.
    """

    read_serializer_class = BusinessLeadSerializer
    write_serializer_class = BusinessLeadSerializer
    filter_backends = (
        DjangoFilterBackend,
    )
    filter_fields = ['company_id']

    def get_queryset(self):
        """
        Returns a queryset of business leads, filtered to those
        associated with the user.
        """
        return BusinessLead.objects.select_related(
            'company',
            'advisor',
            'address_country',
            'archived_by'
        ).filter(
            advisor=self.request.user
        )

    def get_additional_data(self, create):
        """Set advisor to the user on model instance creation."""
        data = {}
        if create:
            data['advisor'] = self.request.user
        return data

"""Business lead views."""

from django_filters.rest_framework import DjangoFilterBackend

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSetV3
from datahub.leads.models import BusinessLead
from datahub.leads.serializers import BusinessLeadSerializer


class BusinessLeadViewSet(ArchivableViewSetMixin, CoreViewSetV3):
    """
    Business lead views.

    Users can only view business leads that are associated with them.
    """

    serializer_class = BusinessLeadSerializer
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
            'adviser',
            'address_country',
            'archived_by'
        ).filter(
            adviser=self.request.user
        )

    def get_additional_data(self, create):
        """Set adviser to the user on model instance creation."""
        data = super().get_additional_data(create)
        if create:
            data['adviser'] = self.request.user
        return data

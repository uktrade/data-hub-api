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
    filter_fields = ['company_id', 'created_by_id']

    def get_queryset(self):
        """
        Returns a queryset of business leads, filtered to those
        associated with the user.
        """
        return BusinessLead.objects.select_related(
            'company',
            'address_country',
            'archived_by',
            'created_by',
            'modified_by',
        )

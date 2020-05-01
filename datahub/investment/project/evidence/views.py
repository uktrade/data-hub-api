from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend

from datahub.documents.views import BaseEntityDocumentModelViewSet
from datahub.investment.project.evidence.models import EvidenceDocument
from datahub.investment.project.evidence.permissions import (
    EvidenceDocumentModelPermissions,
    IsAssociatedToInvestmentProjectEvidenceDocumentPermission,
)
from datahub.investment.project.evidence.serializers import EvidenceDocumentSerializer
from datahub.investment.project.models import InvestmentProject
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.utils import record_user_event


class EvidenceDocumentViewSet(BaseEntityDocumentModelViewSet):
    """Evidence Document ViewSet."""

    non_existent_project_error_message = 'Specified investment project does not exist'

    permission_classes = (
        EvidenceDocumentModelPermissions,
        IsAssociatedToInvestmentProjectEvidenceDocumentPermission,
    )
    serializer_class = EvidenceDocumentSerializer
    queryset = EvidenceDocument.objects.select_related(
        'investment_project',
    ).prefetch_related(
        'tags',
    )

    filter_backends = (
        DjangoFilterBackend,
    )

    def initial(self, request, *args, **kwargs):
        """
        Raise an Http404 if there is no project corresponding to the project ID specified in
        the URL path.
        """
        super().initial(request, *args, **kwargs)

        if not InvestmentProject.objects.filter(pk=self.kwargs['project_pk']).exists():
            raise Http404(self.non_existent_project_error_message)

    def filter_queryset(self, queryset):
        """Filter the queryset to the project specified in the URL path."""
        filtered_queryset = super().filter_queryset(queryset)

        return filtered_queryset.filter(
            investment_project_id=self.kwargs['project_pk'],
        )

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Evidence documents'

    def destroy(self, request, *args, **kwargs):
        """Record delete event."""
        entity_document = self.get_object()
        data = self.serializer_class(entity_document).data
        record_user_event(request, UserEventType.EVIDENCE_DOCUMENT_DELETE, data=data)
        return super().destroy(request, *args, **kwargs)

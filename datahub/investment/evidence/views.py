from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from datahub.documents.views import BaseEntityDocumentModelViewSet
from datahub.investment.evidence.models import EvidenceDocument
from datahub.investment.evidence.permissions import (
    EvidenceDocumentModelPermissions,
    IsAssociatedToInvestmentProjectEvidenceDocumentPermission,
)
from datahub.investment.evidence.serializers import EvidenceDocumentSerializer
from datahub.investment.models import InvestmentProject
from datahub.oauth.scopes import Scope
from datahub.user_event_log.constants import USER_EVENT_TYPES
from datahub.user_event_log.utils import record_user_event


class EvidenceDocumentViewSet(BaseEntityDocumentModelViewSet):
    """Evidence Document ViewSet."""

    non_existent_project_error_message = 'Specified investment project does not exist'

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        EvidenceDocumentModelPermissions,
        IsAssociatedToInvestmentProjectEvidenceDocumentPermission,
    )
    serializer_class = EvidenceDocumentSerializer

    filter_backends = (
        DjangoFilterBackend,
    )

    def get_queryset(self):
        """Returns evidence documents queryset."""
        self._check_project_exists()

        return EvidenceDocument.objects.select_related(
            'investment_project',
        ).prefetch_related(
            'tags',
        ).filter(
            investment_project_id=self.kwargs['project_pk'],
        )

    def create(self, request, *args, **kwargs):
        """Creates evidence document."""
        self._check_project_exists()
        return super().create(request, *args, **kwargs)

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Evidence documents'

    def destroy(self, request, *args, **kwargs):
        """Record delete event."""
        entity_document = self.get_object()
        data = self.serializer_class(entity_document).data
        record_user_event(request, USER_EVENT_TYPES.evidence_document_delete, data=data)
        return super().destroy(request, *args, **kwargs)

    def _check_project_exists(self):
        if not InvestmentProject.objects.filter(pk=self.kwargs['project_pk']).exists():
            raise Http404(self.non_existent_project_error_message)

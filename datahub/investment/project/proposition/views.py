from django.conf import settings
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from datahub.core.exceptions import APIBadRequestException
from datahub.core.viewsets import CoreViewSet
from datahub.documents.views import BaseEntityDocumentModelViewSet
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.proposition.models import Proposition, PropositionDocument
from datahub.investment.project.proposition.permissions import (
    IsAssociatedToInvestmentProjectPropositionDocumentPermission,
    IsAssociatedToInvestmentProjectPropositionPermission,
    PropositionDocumentModelPermissions,
    PropositionModelPermissions,
)
from datahub.investment.project.proposition.serializers import (
    AbandonPropositionSerializer,
    CompletePropositionSerializer,
    CreatePropositionSerializer,
    PropositionDocumentSerializer,
    PropositionSerializer,
)
from datahub.oauth.scopes import Scope
from datahub.user_event_log.constants import USER_EVENT_TYPES
from datahub.user_event_log.utils import record_user_event

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class PropositionViewSet(CoreViewSet):
    """ViewSet for public facing proposition endpoint."""

    non_existent_project_error_message = 'Specified investment project does not exist'

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        PropositionModelPermissions,
        IsAssociatedToInvestmentProjectPropositionPermission,
    )
    serializer_class = PropositionSerializer
    queryset = Proposition.objects.select_related(
        'investment_project',
        'adviser',
        'created_by',
        'modified_by',
    )
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filterset_fields = ('adviser_id', 'status')

    lookup_url_kwarg = 'proposition_pk'

    ordering_fields = ('deadline', 'created_on')
    ordering = ('-deadline', '-created_on')

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

    def create(self, request, *args, **kwargs):
        """Creates proposition."""
        serializer = CreatePropositionSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(**self.get_additional_data(True))
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_201_CREATED,
        )

    def _action(self, method, action_serializer, request, *args, **kwargs):
        """Invokes action for a proposition."""
        if method not in ('abandon', 'complete'):
            raise APIBadRequestException()

        instance = self.get_object()

        serializer = action_serializer(
            instance,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = getattr(serializer, method)()
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_200_OK,
        )

    def complete(self, request, *args, **kwargs):
        """Completes proposition."""
        return self._action('complete', CompletePropositionSerializer, request, *args, **kwargs)

    def abandon(self, request, *args, **kwargs):
        """Abandons proposition."""
        return self._action('abandon', AbandonPropositionSerializer, request, *args, **kwargs)

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        context = {
            **super().get_serializer_context(),
            'current_user': self.request.user if self.request else None,
        }
        return context

    def get_additional_data(self, create):
        """Set investment project id from url parameter."""
        data = super().get_additional_data(create)
        if create:
            data['investment_project_id'] = self.kwargs['project_pk']
        return data


class PropositionDocumentViewSet(BaseEntityDocumentModelViewSet):
    """Proposition Document ViewSet."""

    non_existent_proposition_error_message = 'Specified proposition does not exist'

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        PropositionDocumentModelPermissions,
        IsAssociatedToInvestmentProjectPropositionDocumentPermission,
    )
    serializer_class = PropositionDocumentSerializer
    queryset = PropositionDocument.objects.select_related(
        'proposition__investment_project',
    )

    filter_backends = (
        DjangoFilterBackend,
    )

    def initial(self, request, *args, **kwargs):
        """
        Raise an Http404 if there is no project or proposition corresponding to the IDs
        specified in the URL path.
        """
        super().initial(request, *args, **kwargs)

        proposition_queryset = Proposition.objects.filter(
            pk=self.kwargs['proposition_pk'],
            investment_project_id=self.kwargs['project_pk'],
        )

        if not proposition_queryset.exists():
            raise Http404(self.non_existent_proposition_error_message)

    def filter_queryset(self, queryset):
        """Filter the queryset to the project and proposition specified in the URL path."""
        filtered_queryset = super().filter_queryset(queryset)

        return filtered_queryset.filter(
            proposition_id=self.kwargs['proposition_pk'],
            proposition__investment_project_id=self.kwargs['project_pk'],
        )

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Proposition documents'

    def destroy(self, request, *args, **kwargs):
        """Record delete event."""
        entity_document = self.get_object()
        data = self.serializer_class(entity_document).data
        data['proposition_id'] = entity_document.proposition_id
        record_user_event(request, USER_EVENT_TYPES.proposition_document_delete, data=data)
        return super().destroy(request, *args, **kwargs)

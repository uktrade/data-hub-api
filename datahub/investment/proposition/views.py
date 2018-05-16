from django.conf import settings
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from datahub.core.exceptions import APIBadRequestException
from datahub.core.viewsets import CoreViewSet
from datahub.investment.models import InvestmentProject
from datahub.investment.proposition.models import Proposition
from datahub.investment.proposition.permissions import (
    IsAssociatedToInvestmentProjectPropositionFilter,
    IsAssociatedToInvestmentProjectPropositionPermission,
    PropositionModelPermissions,
)
from datahub.investment.proposition.serializers import (
    CompleteOrAbandonPropositionSerializer,
    CreatePropositionSerializer,
    PropositionSerializer
)
from datahub.oauth.scopes import Scope

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
        IsAssociatedToInvestmentProjectPropositionFilter,
        OrderingFilter,
    )
    filter_fields = ('adviser_id', 'status',)
    ordering_fields = ('deadline', 'created_on',)
    ordering = ('-deadline', '-created_on',)

    def get_queryset(self):
        """Filters the query set to the specified project."""
        self._check_project_exists()

        return self.queryset.filter(
            investment_project_id=self.kwargs['project_pk']
        )

    def create(self, request, *args, **kwargs):
        """Creates proposition."""
        self._check_project_exists()

        serializer = CreatePropositionSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(**self.get_additional_data(True))
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_201_CREATED
        )

    def _action(self, method, request, *args, **kwargs):
        """Invokes action for a proposition."""
        self._check_project_exists()

        if method not in ('abandon', 'complete'):
            raise APIBadRequestException()

        instance = self.get_object()

        serializer = CompleteOrAbandonPropositionSerializer(
            instance,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = getattr(serializer, method)()
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_200_OK
        )

    def complete(self, request, *args, **kwargs):
        """Completes proposition."""
        return self._action('complete', request, *args, **kwargs)

    def abandon(self, request, *args, **kwargs):
        """Abandons proposition."""
        return self._action('abandon', request, *args, **kwargs)

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        context = {
            **super().get_serializer_context(),
            'current_user': self.request.user,
        }
        return context

    def get_additional_data(self, create):
        """Set investment project id from url parameter."""
        data = super().get_additional_data(create)
        if create:
            data['investment_project_id'] = self.kwargs['project_pk']
        return data

    def _check_project_exists(self):
        if not InvestmentProject.objects.filter(pk=self.kwargs['project_pk']).exists():
            raise Http404(self.non_existent_project_error_message)

from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from datahub.core.viewsets import CoreViewSet
from datahub.investment.proposition.models import Proposition
from datahub.investment.proposition.serializers import (
    AbandonPropositionSerializer,
    CompletePropositionSerializer,
    CreatePropositionSerializer,
    PropositionSerializer
)
from datahub.oauth.scopes import Scope

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class PropositionViewSet(CoreViewSet):
    """ViewSet for public facing proposition endpoint."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (IsAuthenticatedOrTokenHasScope,)
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
    filter_fields = ('adviser_id', 'investment_project_id', 'status',)
    ordering_fields = ('deadline', 'created_on',)
    ordering = ('-deadline', '-created_on',)

    def create(self, request, *args, **kwargs):
        """Creates proposition."""
        serializer = CreatePropositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        extra_data = self.get_additional_data(True)
        instance = serializer.save(**extra_data)
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_201_CREATED
        )

    def complete(self, request, *args, **kwargs):
        """Completes proposition."""
        instance = self.get_object()

        serializer = CompletePropositionSerializer(
            instance,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.complete()
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_200_OK
        )

    def abandon(self, request, *args, **kwargs):
        """Abandons proposition."""
        instance = self.get_object()

        serializer = AbandonPropositionSerializer(
            instance,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.abandon()
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_200_OK
        )

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        return {
            **super().get_serializer_context(),
            'current_user': self.request.user,
        }

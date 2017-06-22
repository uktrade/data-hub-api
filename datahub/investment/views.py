"""Investment views."""
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSetV3
from datahub.investment.models import InvestmentProject, IProjectDocument
from datahub.investment.serializers import (
    IProjectAuditSerializer, IProjectDocumentSerializer, IProjectRequirementsSerializer,
    IProjectSerializer, IProjectTeamSerializer, IProjectValueSerializer
)


class IProjectViewSet(ArchivableViewSetMixin, CoreViewSetV3):
    """Investment project views.

    This is a subset of the fields on an InvestmentProject object.
    """

    serializer_class = IProjectSerializer
    queryset = InvestmentProject.objects.select_related(
        'archived_by',
        'investment_type',
        'phase',
        'investor_company',
        'intermediate_company',
        'client_relationship_manager',
        'referral_source_adviser',
        'referral_source_activity',
        'referral_source_activity_website',
        'referral_source_activity_marketing',
        'fdi_type',
        'non_fdi_type',
        'sector'
    ).prefetch_related(
        'client_contacts',
        'business_activities'
    )
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('investor_company_id',)

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment projects'


class IProjectAuditViewSet(CoreViewSetV3):
    """Investment Project audit views."""

    serializer_class = IProjectAuditSerializer
    queryset = InvestmentProject.objects.all()

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment project audit log'


class IProjectValueViewSet(CoreViewSetV3):
    """Investment project value views.

    This is a subset of the fields on an InvestmentProject object.
    """

    serializer_class = IProjectValueSerializer
    queryset = InvestmentProject.objects.select_related('average_salary')

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment project values'


class IProjectRequirementsViewSet(CoreViewSetV3):
    """Investment project requirements views.

    This is a subset of the fields on an InvestmentProject object.
    """

    serializer_class = IProjectRequirementsSerializer
    queryset = InvestmentProject.objects.prefetch_related(
        'competitor_countries',
        'uk_region_locations',
        'strategic_drivers'
    )

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment project requirements'


class IProjectTeamViewSet(CoreViewSetV3):
    """Investment project team views.

    This is a subset of the fields on an InvestmentProject object.
    """

    serializer_class = IProjectTeamSerializer
    queryset = InvestmentProject.objects.select_related(
        'project_manager',
        'project_manager__dit_team',
        'project_assurance_adviser',
        'project_assurance_adviser__dit_team'
    )

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment project teams'


class IProjectDocumentViewSet(CoreViewSetV3):
    """Investment Project Documents ViewSet."""

    serializer_class = IProjectDocumentSerializer
    queryset = IProjectDocument.objects.all()

    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('doc_type',)

    def list(self, request, *args, **kwargs):
        """Custom pre-filtered list."""
        queryset = self.filter_queryset(self.get_queryset().filter(project_id=self.kwargs['project_pk']))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create and one-time upload URL generation."""
        response = super().create(request, *args, **kwargs)
        document = IProjectDocument.objects.get(pk=response.data['id'])

        response.data['signed_upload_url'] = document.signed_upload_url

        return response

    def get_object(self):
        """Ensures that object lookup honors the project pk."""
        queryset = self.get_queryset().filter(project__id=self.kwargs['project_pk'])
        queryset = self.filter_queryset(queryset)

        obj = get_object_or_404(queryset, pk=self.kwargs['doc_pk'])
        self.check_object_permissions(self.request, obj)

        return obj

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment project documents'

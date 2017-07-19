"""Investment views."""
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.serializers import AuditSerializer
from datahub.core.utils import executor
from datahub.core.viewsets import CoreViewSetV3
from datahub.documents.av_scan import virus_scan_document
from datahub.investment.models import (
    InvestmentProject, InvestmentProjectTeamMember, IProjectDocument
)
from datahub.investment.serializers import (
    IProjectDocumentSerializer, IProjectSerializer, IProjectTeamMemberSerializer,
    UploadStatusSerializer
)


class IProjectAuditViewSet(CoreViewSetV3):
    """Investment Project audit views."""

    serializer_class = AuditSerializer
    queryset = InvestmentProject.objects.all()

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment project audit log'


class IProjectViewSet(ArchivableViewSetMixin, CoreViewSetV3):
    """Unified investment project views.

    This replaces the previous project, value, team and requirements endpoints.
    """

    serializer_class = IProjectSerializer
    queryset = InvestmentProject.objects.select_related(
        'archived_by',
        'investment_type',
        'stage',
        'investor_company',
        'intermediate_company',
        'client_relationship_manager',
        'referral_source_adviser',
        'referral_source_activity',
        'referral_source_activity_website',
        'referral_source_activity_marketing',
        'fdi_type',
        'non_fdi_type',
        'sector',
        'average_salary',
        'project_manager',
        'project_manager__dit_team',
        'project_assurance_adviser',
        'project_assurance_adviser__dit_team'
    ).prefetch_related(
        'client_contacts',
        'business_activities',
        'competitor_countries',
        'uk_region_locations',
        'strategic_drivers',
    )
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('investor_company_id',)

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment projects'


class IProjectTeamMembersViewSet(CoreViewSetV3):
    """Investment project team member views."""

    serializer_class = IProjectTeamMemberSerializer
    lookup_field = 'adviser_id'
    lookup_url_kwarg = 'adviser_pk'
    queryset = InvestmentProjectTeamMember.objects.select_related('adviser')

    def get_queryset(self):
        """Filters the query set to the specified project."""
        self._check_project_exists()
        return self.queryset.filter(
            investment_project_id=self.kwargs['project_pk']
        ).all()

    def get_serializer(self, *args, **kwargs):
        """Gets a serializer instance.

        Adds the investment_project_id from the URL path to the user-provided data.
        """
        data = kwargs.get('data')
        if data is not None:
            data['investment_project'] = self.kwargs['project_pk']
        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Creates a team member instance.

        Ensures a 404 is returned if the specified project does not exist.
        """
        self._check_project_exists()
        return super().create(request, *args, **kwargs)

    def destroy_all(self, request, *args, **kwargs):
        """Removes all team members from the specified project."""
        queryset = self.get_queryset()
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment project team members'

    def _check_project_exists(self):
        if not InvestmentProject.objects.filter(pk=self.kwargs['project_pk']).exists():
            raise Http404('Specified investment project does not exist')


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

    def upload_complete_callback(self, request, *args, **kwargs):
        """File upload done callback."""
        doc = self.get_object()
        serializer = UploadStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        executor.submit(virus_scan_document, str(doc.pk))

        return Response(
            status=status.HTTP_200_OK,
            data={
                'status': 'accepted',
            },
        )

    def perform_destroy(self, instance):
        """Perform destroy in transaction/savepoint mode."""
        with transaction.atomic():
            return super().perform_destroy(instance)

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

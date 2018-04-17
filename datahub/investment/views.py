"""Investment views."""
from django.db import transaction
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters import IsoDateTimeFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import BasePagination
from rest_framework.response import Response

from datahub.core.audit import AuditViewSet
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.thread_pool import submit_to_thread_pool
from datahub.core.viewsets import CoreViewSet
from datahub.documents.av_scan import virus_scan_document
from datahub.investment.models import (
    InvestmentProject, InvestmentProjectTeamMember, IProjectDocument
)
from datahub.investment.permissions import (
    InvestmentProjectModelPermissions, InvestmentProjectTeamMemberModelPermissions,
    IsAssociatedToInvestmentProjectFilter, IsAssociatedToInvestmentProjectPermission,
    IsAssociatedToInvestmentProjectTeamMemberPermission,
)
from datahub.investment.serializers import (
    IProjectDocumentSerializer, IProjectSerializer, IProjectTeamMemberSerializer,
    UploadStatusSerializer
)
from datahub.oauth.scopes import Scope

_team_member_queryset = InvestmentProjectTeamMember.objects.select_related('adviser')


class IProjectAuditViewSet(AuditViewSet):
    """Investment Project audit views."""

    required_scopes = (Scope.internal_front_end,)
    queryset = InvestmentProject.objects.all()
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        InvestmentProjectModelPermissions,
        IsAssociatedToInvestmentProjectPermission,
    )

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment project audit log'


class IProjectViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Unified investment project views.

    This replaces the previous project, value, team and requirements endpoints.
    """

    permission_classes = (IsAuthenticatedOrTokenHasScope, InvestmentProjectModelPermissions,
                          IsAssociatedToInvestmentProjectPermission)
    required_scopes = (Scope.internal_front_end,)
    serializer_class = IProjectSerializer
    queryset = InvestmentProject.objects.select_related(
        'archived_by',
        'investment_type',
        'stage',
        'investor_company',
        'investor_type',
        'intermediate_company',
        'level_of_involvement',
        'specific_programme',
        'uk_company',
        'uk_company__registered_address_country',
        'investmentprojectcode',
        'client_relationship_manager',
        'client_relationship_manager__dit_team',
        'referral_source_adviser',
        'referral_source_activity',
        'referral_source_activity_website',
        'referral_source_activity_marketing',
        'fdi_type',
        'average_salary',
        'project_manager',
        'project_manager__dit_team',
        'project_assurance_adviser',
        'project_assurance_adviser__dit_team',
        'country_lost_to',
    ).prefetch_related(
        'actual_uk_regions',
        'client_contacts',
        'business_activities',
        'competitor_countries',
        'delivery_partners',
        'uk_region_locations',
        'sector',
        'sector__parent',
        'sector__parent__parent',
        'strategic_drivers',
        Prefetch('team_members', queryset=_team_member_queryset),
    )
    filter_backends = (DjangoFilterBackend,
                       OrderingFilter,
                       IsAssociatedToInvestmentProjectFilter)
    filter_fields = ('investor_company_id',)
    ordering = ('-created_on',)

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment projects'


class _ModifiedOnFilter(FilterSet):
    """Filter set for the modified-since view."""

    modified_on__gte = IsoDateTimeFilter(field_name='modified_on', lookup_expr='gte')
    modified_on__lte = IsoDateTimeFilter(field_name='modified_on', lookup_expr='lte')

    class Meta:
        model = InvestmentProject
        fields = ()


class _SinglePagePaginator(BasePagination):
    """Paginator that returns all items in a single page.

    The purpose of this is to wrap the results in a dict with count and results keys,
    for consistency with other endpoints.
    """

    def paginate_queryset(self, queryset, request, view=None):
        return queryset

    def get_paginated_response(self, data):
        return Response({
            'count': len(data),
            'results': data
        })


class IProjectModifiedSinceViewSet(IProjectViewSet):
    """View set for the modified-since endpoint (intended for use by Data Hub MI)."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.mi,)
    pagination_class = _SinglePagePaginator

    filter_backends = (DjangoFilterBackend,)
    filter_fields = None
    filter_class = _ModifiedOnFilter


class IProjectTeamMembersViewSet(CoreViewSet):
    """Investment project team member views."""

    non_existent_project_error_message = 'Specified investment project does not exist'
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        InvestmentProjectTeamMemberModelPermissions,
        IsAssociatedToInvestmentProjectTeamMemberPermission,
    )
    required_scopes = (Scope.internal_front_end,)
    serializer_class = IProjectTeamMemberSerializer
    lookup_field = 'adviser_id'
    lookup_url_kwarg = 'adviser_pk'
    queryset = _team_member_queryset

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
        self._update_serializer_data_with_project(*args, **kwargs)
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

    def replace_all(self, request, *args, **kwargs):
        """Replaces all team members in the specified project."""
        self._check_project_exists()
        queryset = self.get_queryset()

        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            serializer.update(queryset, serializer.validated_data)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment project team members'

    def get_project(self):
        """Gets the investment project object referred to in the URL path."""
        try:
            return InvestmentProject.objects.get(pk=self.kwargs['project_pk'])
        except InvestmentProject.DoesNotExist:
            raise Http404(self.non_existent_project_error_message)

    def _update_serializer_data_with_project(self, *args, data=None, many=False, **kwargs):
        if data is not None:
            project_pk = str(self.kwargs['project_pk'])
            items = data if many else [data]
            for item in items:
                item['investment_project'] = project_pk

    def _check_project_exists(self):
        if not InvestmentProject.objects.filter(pk=self.kwargs['project_pk']).exists():
            raise Http404(self.non_existent_project_error_message)


class IProjectDocumentViewSet(CoreViewSet):
    """Investment Project Documents ViewSet."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = IProjectDocumentSerializer
    queryset = IProjectDocument.objects.all()

    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('doc_type',)

    def list(self, request, *args, **kwargs):
        """Custom pre-filtered list."""
        queryset = self.filter_queryset(self.get_queryset().filter(
            project_id=self.kwargs['project_pk'])
        )

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

        submit_to_thread_pool(virus_scan_document, str(doc.pk))

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

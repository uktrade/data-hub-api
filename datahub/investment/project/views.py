"""Investment views."""
from django.db import transaction
from django.db.models import Prefetch
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, IsoDateTimeFilter
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import BasePagination
from rest_framework.response import Response

from datahub.core.audit import AuditViewSet
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.investment.project.models import InvestmentProject, InvestmentProjectTeamMember
from datahub.investment.project.permissions import (
    InvestmentProjectModelPermissions,
    InvestmentProjectTeamMemberModelPermissions,
    IsAssociatedToInvestmentProjectFilter,
    IsAssociatedToInvestmentProjectPermission,
    IsAssociatedToInvestmentProjectTeamMemberPermission,
)
from datahub.investment.project.serializers import (
    InvestmentActivitySerializer,
    IProjectSerializer,
    IProjectTeamMemberSerializer,
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

    @classmethod
    def _get_additional_change_information(cls, v_new):
        """
        Gets any investment activity associated with a change for the a change log entry.
        If a note is not present then returns a None for a note to follow
        the same behaviour as DRF.
        """
        if hasattr(v_new.revision, 'investmentactivity'):
            return {'note': cls.get_activity_data(v_new.revision.investmentactivity)}
        return {'note': None}

    @classmethod
    def get_activity_data(cls, activity):
        """Returns the serialized data of an investment activity instance."""
        return InvestmentActivitySerializer(activity).data


class IProjectViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Unified investment project views.

    This replaces the previous project, value, team and requirements endpoints.
    """

    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        InvestmentProjectModelPermissions,
        IsAssociatedToInvestmentProjectPermission,
    )
    required_scopes = (Scope.internal_front_end,)
    serializer_class = IProjectSerializer
    queryset = InvestmentProject.objects.select_related(
        'archived_by',
        'average_salary',
        'client_relationship_manager__dit_team',
        'client_relationship_manager',
        'country_lost_to',
        'fdi_type',
        'intermediate_company',
        'investment_type',
        'investmentprojectcode',
        'investor_company',
        'investor_type',
        'level_of_involvement',
        'project_assurance_adviser__dit_team',
        'project_assurance_adviser',
        'project_manager__dit_team',
        'project_manager',
        'referral_source_activity_marketing',
        'referral_source_activity_website',
        'referral_source_activity',
        'referral_source_adviser',
        'specific_programme',
        'stage',
        'uk_company__address_country',
        'uk_company',
    ).prefetch_related(
        'actual_uk_regions',
        'business_activities',
        'client_contacts',
        'competitor_countries',
        'delivery_partners',
        'sector__parent__parent',
        'sector__parent',
        'sector',
        'strategic_drivers',
        'uk_region_locations',
        Prefetch('team_members', queryset=_team_member_queryset),
    )
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
        IsAssociatedToInvestmentProjectFilter,
    )
    filterset_fields = ('investor_company_id',)
    ordering = ('-created_on',)

    def get_view_name(self):
        """Returns the view set name for the DRF UI."""
        return 'Investment projects'

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        return {
            **super().get_serializer_context(),
            'current_user': self.request.user if self.request else None,
        }


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
            'results': data,
        })


class IProjectModifiedSinceViewSet(IProjectViewSet):
    """View set for the modified-since endpoint (intended for use by Data Hub MI)."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.mi,)
    pagination_class = _SinglePagePaginator

    filter_backends = (DjangoFilterBackend,)
    filterset_fields = None
    filterset_class = _ModifiedOnFilter


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

    def initial(self, request, *args, **kwargs):
        """Raise an Http404 if the project referenced in the URL path does not exist."""
        super().initial(request, *args, **kwargs)

        if not InvestmentProject.objects.filter(pk=self.kwargs['project_pk']).exists():
            raise Http404(self.non_existent_project_error_message)

    def get_queryset(self):
        """Filters the query set to the specified project."""
        return self.queryset.filter(
            investment_project_id=self.kwargs['project_pk'],
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
        return super().create(request, *args, **kwargs)

    def destroy_all(self, request, *args, **kwargs):
        """Removes all team members from the specified project."""
        queryset = self.get_queryset()
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def replace_all(self, request, *args, **kwargs):
        """Replaces all team members in the specified project."""
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
        """
        Gets the investment project object referred to in the URL path.

        This is used by IsAssociatedToInvestmentProjectTeamMemberPermission (which handles a
        non-existent project correctly).

        Note: self.kwargs will not be populated during view schema introspection.
        """
        try:
            return InvestmentProject.objects.get(pk=self.kwargs['project_pk'])
        except (InvestmentProject.DoesNotExist, KeyError):
            return None

    def _update_serializer_data_with_project(self, *args, data=None, many=False, **kwargs):
        if data is not None:
            project_pk = str(self.kwargs['project_pk'])
            items = data if many else [data]
            for item in items:
                item['investment_project'] = project_pk

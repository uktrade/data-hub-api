"""Investment views."""
from django.db import transaction
from django.db.models import Prefetch
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from datahub.core.audit import AuditViewSet
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.permissions import HasPermissions
from datahub.core.schemas import StubSchema
from datahub.core.viewsets import CoreViewSet
from datahub.investment.project.models import (
    InvestmentProject,
    InvestmentProjectPermission,
    InvestmentProjectTeamMember,
)
from datahub.investment.project.permissions import (
    InvestmentProjectModelPermissions,
    InvestmentProjectTeamMemberModelPermissions,
    IsAssociatedToInvestmentProjectFilter,
    IsAssociatedToInvestmentProjectPermission,
    IsAssociatedToInvestmentProjectTeamMemberPermission,
)
from datahub.investment.project.serializers import (
    InvestmentActivitySerializer,
    IProjectChangeStageSerializer,
    IProjectSerializer,
    IProjectTeamMemberSerializer,
)


_team_member_queryset = InvestmentProjectTeamMember.objects.select_related('adviser')


class IProjectAuditViewSet(AuditViewSet):
    """Investment Project audit views."""

    queryset = InvestmentProject.objects.all()
    permission_classes = (
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
        InvestmentProjectModelPermissions,
        IsAssociatedToInvestmentProjectPermission,
    )
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

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[
            HasPermissions(f'investment.{InvestmentProjectPermission.change_to_any_stage}'),
        ],
        filter_backends=[],
        schema=StubSchema(),
    )
    def change_stage(self, request, *args, **kwargs):
        """Change the stage of an investment project"""
        instance = self.get_object()
        serializer = IProjectChangeStageSerializer(
            instance,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.change_stage(user=self.request.user)
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_200_OK,
        )


class IProjectTeamMembersViewSet(CoreViewSet):
    """Investment project team member views."""

    non_existent_project_error_message = 'Specified investment project does not exist'
    permission_classes = (
        InvestmentProjectTeamMemberModelPermissions,
        IsAssociatedToInvestmentProjectTeamMemberPermission,
    )
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

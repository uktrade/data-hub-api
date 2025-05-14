"""Company and related resources view sets."""

from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.db.models import Exists, Prefetch, Q
from django.db.models.functions import Lower
from django.http import Http404
from django_filters.rest_framework import (
    CharFilter,
    DateFromToRangeFilter,
    DjangoFilterBackend,
    FilterSet,
    MultipleChoiceFilter,
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from config.settings.types import HawkScope
from datahub.company.autocomplete import WithListAutocompleteFilter
from datahub.company.models import (
    Advisor,
    Company,
    CompanyExport,
    CompanyPermission,
    Contact,
    Objective,
)
from datahub.company.pagination import ContactPageSize
from datahub.company.permissions import IsAccountManagerOnCompany
from datahub.company.queryset import (
    get_contact_queryset,
    get_export_country_queryset,
)
from datahub.company.serializers import (
    AdviserSerializer,
    AssignOneListTierAndGlobalAccountManagerSerializer,
    AssignRegionalAccountManagerSerializer,
    CompanyExportSerializer,
    CompanySerializer,
    ContactSerializer,
    ContactV4Serializer,
    ObjectiveV4Serializer,
    OneListCoreTeamMemberSerializer,
    PublicCompanySerializer,
    RemoveAccountManagerSerializer,
    RemoveCompanyFromOneListSerializer,
    SelfAssignAccountManagerSerializer,
    UpdateExportDetailsSerializer,
    UpdateOneListCoreTeamMembersSerializer,
)
from datahub.company.validators import NotATransferredCompanyValidator
from datahub.company_activity.models import KingsAwardRecipient
from datahub.company_activity.serializers.kings_award import KingsAwardRecipientSerializer
from datahub.core.audit import AuditViewSet
from datahub.core.auth import PaaSIPAuthentication
from datahub.core.autocomplete import AutocompleteFilter
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.permissions import HasPermissions
from datahub.core.schemas import StubSchema
from datahub.core.viewsets import CoreViewSet, SoftDeleteCoreViewSet
from datahub.export_win.models import Win
from datahub.export_win.serializers import DataHubLegacyExportWinSerializer
from datahub.export_win.views import ConfirmedFilterSet
from datahub.investment.project.queryset import get_slim_investment_project_queryset


class CompanyFilterSet(FilterSet):
    """Company filter."""

    autocomplete = WithListAutocompleteFilter(search_fields=('name',))

    class Meta:
        model = Company
        fields = ['global_headquarters_id', 'global_ultimate_duns_number']


class CompanyViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Company view set."""

    serializer_class = CompanySerializer
    unarchive_validators = (NotATransferredCompanyValidator(),)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = CompanyFilterSet
    ordering_fields = ('name', 'created_on')
    queryset = Company.objects.select_related(
        'address_country',
        'archived_by',
        'business_type',
        'employee_range',
        'export_experience_category',
        'global_headquarters__one_list_account_owner__dit_team__country',
        'global_headquarters__one_list_account_owner__dit_team__uk_region',
        'global_headquarters__one_list_account_owner__dit_team',
        'global_headquarters__one_list_account_owner',
        'global_headquarters__one_list_tier',
        'global_headquarters',
        'headquarter_type',
        'one_list_account_owner__dit_team__country',
        'one_list_account_owner__dit_team__uk_region',
        'one_list_account_owner__dit_team',
        'one_list_account_owner',
        'one_list_tier',
        'registered_address_country',
        'transferred_to',
        'turnover_range',
        'uk_region',
    ).prefetch_related(
        Prefetch('contacts', queryset=get_contact_queryset()),
        Prefetch('investor_investment_projects', queryset=get_slim_investment_project_queryset()),
        'export_to_countries',
        'future_interest_countries',
        'sector__parent__parent',
        'sector__parent',
        'sector',
        Prefetch('export_countries', queryset=get_export_country_queryset()),
    )

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[
            HasPermissions(
                f'company.{CompanyPermission.change_company}',
                f'company.{CompanyPermission.change_regional_account_manager}',
            ),
        ],
        schema=StubSchema(),
    )
    def assign_regional_account_manager(self, request, *args, **kwargs):
        """Sets the company to be an international trade adviser-managed One List company, and
        assigns the requested user as the account manager.

        This means:

        - setting the One List tier to 'Tier D - Interaction Trade Adviser Accounts' (using the
        tier ID, not the name)
        - setting the requested user as the One List account manager (overwriting the
        existing value)

        The operation is not allowed if:

        - the company is a subsidiary of a One List company
        - the company is already a One List company on a different tier (i.e. not 'Tier D -
        Interaction Trade Adviser Accounts')
        """
        instance = self.get_object()
        serializer = AssignRegionalAccountManagerSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[
            HasPermissions(
                f'company.{CompanyPermission.change_company}',
                f'company.{CompanyPermission.change_regional_account_manager}',
            ),
        ],
        schema=StubSchema(),
    )
    def self_assign_account_manager(self, request, *args, **kwargs):
        """Sets the company to be an international trade adviser-managed One List company, and
        assigns the authenticated user as the account manager.

        This means:

        - setting the One List tier to 'Tier D - Interaction Trade Adviser Accounts' (using the
        tier ID, not the name)
        - setting the authenticated user as the One List account manager (overwriting the
        existing value)

        The operation is not allowed if:

        - the company is a subsidiary of a One List company
        - the company is already a One List company on a different tier (i.e. not 'Tier D -
        Interaction Trade Adviser Accounts')
        """
        instance = self.get_object()
        serializer = SelfAssignAccountManagerSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[
            HasPermissions(
                f'company.{CompanyPermission.change_company}',
                f'company.{CompanyPermission.change_regional_account_manager}',
            ),
        ],
        schema=StubSchema(),
    )
    def remove_account_manager(self, request, *args, **kwargs):
        """Remove the One List account manager and tier from a company if it is an international
        trade adviser-managed One List company.

        The operation is not allowed if the company is a One List company that isn't on
        'Tier D - Interaction Trade Adviser Accounts'.
        """
        instance = self.get_object()
        serializer = RemoveAccountManagerSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[
            IsAccountManagerOnCompany
            | HasPermissions(
                f'company.{CompanyPermission.change_company}',
                f'company.{CompanyPermission.change_one_list_tier_and_global_account_manager}',
            ),
        ],
        schema=StubSchema(),
    )
    def assign_one_list_tier_and_global_account_manager(self, request, *args, **kwargs):
        """Assign One List tier and Global Account Manager.

        This endpoint enables a user with correct permissions to assign company one list tier
        and global account manager except when company is on
        'Tier D - Interaction Trade Adviser Accounts'.

        One List tier and Global Account Manager cannot be assigned to a subsidiary.
        """
        instance = self.get_object()
        serializer = AssignOneListTierAndGlobalAccountManagerSerializer(
            instance=instance,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[
            HasPermissions(
                f'company.{CompanyPermission.change_company}',
                f'company.{CompanyPermission.change_one_list_tier_and_global_account_manager}',
            ),
        ],
        schema=StubSchema(),
    )
    def remove_from_one_list(self, request, *args, **kwargs):
        """Remove company from One List.

        The operation is not allowed if the company is on
        'Tier D - Interaction Trade Adviser Accounts'.
        """
        instance = self.get_object()
        serializer = RemoveCompanyFromOneListSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['patch'],
        detail=True,
        permission_classes=[
            IsAccountManagerOnCompany
            | HasPermissions(
                f'company.{CompanyPermission.change_company}',
                f'company.{CompanyPermission.change_one_list_core_team_member}',
            )
            | HasPermissions(
                f'company.{CompanyPermission.change_company}',
                f'company.{CompanyPermission.change_one_list_tier_and_global_account_manager}',
            ),
        ],
        schema=StubSchema(),
    )
    def update_one_list_core_team(self, request, *args, **kwargs):
        """Updates core team for the company."""
        instance = self.get_object()
        serializer = UpdateOneListCoreTeamMembersSerializer(
            instance=instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['patch'],
        permission_classes=[
            HasPermissions(
                f'company.{CompanyPermission.change_company}',
                'company.change_companyexportcountry',
            ),
        ],
        detail=True,
    )
    def update_export_detail(self, request, *args, **kwargs):
        """Update export related information for the company."""
        instance = self.get_object()
        serializer = UpdateExportDetailsSerializer(
            instance=instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[HasPermissions(f'company.{CompanyPermission.view_company}')],
        serializer_class=KingsAwardRecipientSerializer,
        url_path='kings-awards',
    )
    def kings_awards(self, request, pk):
        """Returns a list of King's Awards received by this company."""
        company = self.get_object()
        queryset = (
            KingsAwardRecipient.objects.filter(company=company)
            .select_related(
                'company',
            )
            .order_by('-year_awarded')
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PublicCompanyViewSet(HawkResponseSigningMixin, mixins.RetrieveModelMixin, GenericViewSet):
    """Read-only company view set using Hawk-authentication (with no user context)."""

    serializer_class = PublicCompanySerializer
    authentication_classes = (PaaSIPAuthentication, HawkAuthentication)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.public_company

    queryset = Company.objects.select_related(
        'address_country',
        'archived_by',
        'business_type',
        'employee_range',
        'export_experience_category',
        'global_headquarters',
        'global_headquarters__one_list_tier',
        'headquarter_type',
        'one_list_tier',
        'registered_address_country',
        'transferred_to',
        'turnover_range',
        'uk_region',
    ).prefetch_related(
        'export_to_countries',
        'future_interest_countries',
        'sector',
        'sector__parent',
        'sector__parent__parent',
    )


class OneListGroupCoreTeamViewSet(CoreViewSet):
    """Views for the One List Core Team of the group a company is part of.
    A Core Team is usually assigned to the Global Headquarters and is shared among all
    members of the group.

    The permissions to access this resource are inherited from the company resource.

    E.g. user only needs `view_company` permission to GET this collection and
    onelistcoreteammember permissions are ignored for now.
    """

    queryset = Company.objects
    serializer_class = OneListCoreTeamMemberSerializer

    def list(self, request, *args, **kwargs):
        """Lists Core Team members."""
        company = self.get_object()
        core_team = company.get_one_list_group_core_team()

        serializer = self.get_serializer(core_team, many=True)
        return Response(serializer.data)


class CompanyAuditViewSet(AuditViewSet):
    """Company audit views."""

    queryset = Company.objects.prefetch_related(
        Prefetch('one_list_core_team_members', to_attr='one_list_core_team_members_changes'),
    ).all()

    @classmethod
    def _pre_process_version_list(cls, versions):
        """Include changes to One list core team members."""
        for version in versions:
            one_list_core_team_members = version.revision.version_set.all().filter(
                content_type__model='onelistcoreteammember',
            )
            version.field_dict['one_list_core_team_members'] = []
            for one_list_core_team_member in one_list_core_team_members:
                version.field_dict['one_list_core_team_members'].append(
                    one_list_core_team_member.object.adviser.name
                    if one_list_core_team_member.object
                    else one_list_core_team_member.object_repr.split(' - ')[0],
                )

            version.field_dict['one_list_core_team_members'].sort()
        return versions


class ContactViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Contact ViewSet v3."""

    serializer_class = ContactSerializer
    queryset = get_contact_queryset()
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filterset_fields = ['company_id', 'email', 'archived']
    ordering = ('-created_on',)

    def get_additional_data(self, create):
        """Set adviser to the user on model instance creation."""
        data = super().get_additional_data(create)
        if create:
            data['adviser'] = self.request.user
        return data


class ContactV4ViewSet(ContactViewSet):
    """Contact ViewSet v4."""

    serializer_class = ContactV4Serializer
    pagination_class = ContactPageSize


class ContactAuditViewSet(AuditViewSet):
    """Contact audit views."""

    queryset = Contact.objects.all()


def _build_permission_filter(app_label, codename):
    """Create a Q object that checks if an adviser has a particular permission.

    All possible places permissions could be stored are checked:

    - directly on the user
    - in the users' groups
    - in the user's team role's groups
    """
    all_matching_permissions = Permission.objects.filter(
        content_type__app_label=app_label,
        codename=codename,
    ).order_by()

    matching_permission = all_matching_permissions[:1]

    # Use a subquery for groups as joining on the permissions table is very inefficient
    groups_with_permission = Group.objects.filter(
        permissions=matching_permission,
    )

    return Exists(all_matching_permissions) & (
        Q(is_superuser=True)
        | Q(user_permissions=matching_permission)
        | Q(groups__in=groups_with_permission)
        | Q(dit_team__role__groups__in=groups_with_permission)
    )


class AdviserFilter(FilterSet):
    """Adviser filter."""

    autocomplete = AutocompleteFilter(
        search_fields=('first_name', 'last_name', 'dit_team__name'),
    )
    permissions__has = CharFilter(method='filter_permissions__has')

    @staticmethod
    def filter_permissions__has(queryset, field_name, value):
        """Filter advisers by a single permission (e.g. filter to advisers with the
        'company.add_company' permission).

        Note: An adviser could have the same permission multiple times (in different
        locations) and so duplicates need be avoided when this is the case. This is
        done by using a subquery.
        """
        app_label, _, codename = value.partition('.')
        q = _build_permission_filter(app_label, codename)
        subquery = Advisor.objects.filter(q).values('pk')

        return queryset.filter(pk__in=subquery)

    class Meta:
        model = Advisor
        fields = {
            'is_active': ('exact',),
            'dit_team__role': ('exact',),
        }


class AdviserReadOnlyViewSetV1(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Adviser GET only views."""

    serializer_class = AdviserSerializer
    queryset = Advisor.objects.select_related(
        'dit_team',
    )
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filterset_class = AdviserFilter
    ordering_fields = ('first_name', 'last_name', 'dit_team__name')
    _default_ordering = (Lower('first_name'), Lower('last_name'), Lower('dit_team__name'))

    def filter_queryset(self, queryset):
        """Applies the default ordering when the query set has not already been ordered.

        (The autocomplete filter automatically applies an ordering, hence we only set the
        default ordering when another one has not already been set.)
        """
        filtered_queryset = super().filter_queryset(queryset)

        if not filtered_queryset.ordered:
            return filtered_queryset.order_by(*self._default_ordering)

        return filtered_queryset


class ExportWinsForCompanyView(ListAPIView):
    """Export Wins for Company. The view is based on the legacy view that used
    external system storing export wins. They are now migrated to Data Hub so there
    is no need for that.
    """

    permission_classes = (
        HasPermissions(
            f'company.{CompanyPermission.view_export_win}',
        ),
    )
    serializer_class = DataHubLegacyExportWinSerializer
    http_method_names = ('get',)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ConfirmedFilterSet
    ordering_fields = ('customer_response__responded_on', 'created_on')
    ordering = ('-customer_response__responded_on', '-created_on')

    def _get_company(self, company_pk):
        """Returns the company for given pk
        raises Http404 if it doesn't exist.
        """
        try:
            return Company.objects.get(pk=company_pk)
        except Company.DoesNotExist:
            raise Http404

    def get_queryset(self):
        company = self._get_company(self.kwargs['pk'])
        return Win.objects.filter(company=company).order_by('-created_on')


class CompanyExportEstimatedWinDateFilterSet(FilterSet):
    """CompanyExport estimated win date filter."""

    estimated_win_date = DateFromToRangeFilter(
        field_name='estimated_win_date',
    )
    status = MultipleChoiceFilter(
        field_name='status',
        choices=CompanyExport.ExportStatus.choices,
    )
    export_potential = MultipleChoiceFilter(
        field_name='export_potential',
        choices=CompanyExport.ExportPotential.choices,
    )

    class Meta:
        model = CompanyExport
        fields = [
            'archived',
            'destination_country',
            'estimated_win_date',
            'export_potential',
            'owner',
            'sector',
            'status',
            'team_members',
        ]


class CompanyExportViewSet(SoftDeleteCoreViewSet):
    """View for company exports."""

    queryset = CompanyExport.objects.select_related(
        'company',
        'owner',
        'estimated_export_value_years',
        'exporter_experience',
    )
    serializer_class = CompanyExportSerializer
    permission_classes = [
        IsAuthenticated,
    ]
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filterset_class = CompanyExportEstimatedWinDateFilterSet
    ordering_fields = (
        'company__name',
        'estimated_win_date',
        'estimated_export_value_amount',
        'created_on',
        'title',
    )
    ordering = (
        '-created_on',
        'title',
    )

    def get_queryset(self):
        """Filter the queryset to the authenticated user."""
        if self.action == 'list':
            return (
                super()
                .get_queryset()
                .exclude(~Q(owner=self.request.user), ~Q(team_members=self.request.user))
            )

        return super().get_queryset()


class SingleObjectiveV4ViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Single Objective ViewSet v4."""

    permission_classes = [
        IsAuthenticated,
    ]

    queryset = Objective.objects.all().select_related(
        'company',
        'archived_by',
        'modified_by',
    )
    serializer_class = ObjectiveV4Serializer


class CompanyObjectiveV4ViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Objectives for a single company  ViewSet v4."""

    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = ObjectiveV4Serializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['target_date']
    ordering = ['target_date']
    filterset_fields = ['archived']

    def get_queryset(self):
        """Returns a list of all the objectives associated
        with a specific company.
        """
        company_id = self.kwargs['company_id']
        return Objective.objects.filter(company=company_id).select_related(
            'company',
            'archived_by',
            'modified_by',
        )


class CompanyObjectiveArchivedCountV4ViewSet(APIView):
    """Objectives for getting archived counts of objectives for a company."""

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, company_id):
        archived_count = Objective.objects.filter(company=company_id, archived=True).count()
        not_archived_count = Objective.objects.filter(company=company_id, archived=False).count()

        return Response(
            {
                'archived_count': archived_count,
                'not_archived_count': not_archived_count,
            },
        )


@transaction.non_atomic_requests
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def owner_list(request):
    """Returns a list of owners. The list includes users that own an export, if the user
    is a team member of an export then the owner of that export is also included in
    the list of owners. An owner should only appear once in the list - no duplicates.
    """
    advisers = Advisor.objects.all()

    # All company exports where the user is either an owner or a team member
    company_exports = CompanyExport.objects.exclude(
        ~Q(owner=request.user),
        ~Q(team_members=request.user),
    )

    # Pullout all owner ids (no duplicates)
    owner_ids = set()
    for company_export in company_exports:
        owner_ids.add(company_export.owner_id)

    advisers = Advisor.objects.filter(id__in=owner_ids)
    serializer = AdviserSerializer(advisers, many=True)

    return Response(serializer.data)

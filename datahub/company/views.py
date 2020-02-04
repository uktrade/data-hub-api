"""Company and related resources view sets."""
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from config.settings.types import HawkScope
from datahub.company.autocomplete import AutocompleteFilter
from datahub.company.models import (
    Advisor,
    Company,
    CompanyPermission,
    Contact,
)
from datahub.company.queryset import (
    get_contact_queryset,
    get_export_country_queryset,
)
from datahub.company.serializers import (
    AdviserSerializer,
    CompanySerializer,
    ContactSerializer,
    OneListCoreTeamMemberSerializer,
    PublicCompanySerializer,
    RemoveAccountManagerSerializer,
    SelfAssignAccountManagerSerializer,
    UpdateExportDetailsSerializer,
)
from datahub.company.validators import NotATransferredCompanyValidator
from datahub.core.audit import AuditViewSet
from datahub.core.auth import PaaSIPAuthentication
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.permissions import HasPermissions
from datahub.core.schemas import StubSchema
from datahub.core.viewsets import CoreViewSet
from datahub.investment.project.queryset import get_slim_investment_project_queryset
from datahub.oauth.scopes import Scope


class CompanyViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Company view set."""

    serializer_class = CompanySerializer
    required_scopes = (Scope.internal_front_end,)
    unarchive_validators = (NotATransferredCompanyValidator(),)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ('global_headquarters_id', 'global_ultimate_duns_number')
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
    def self_assign_account_manager(self, request, *args, **kwargs):
        """
        Sets the company to be an international trade adviser-managed One List company, and
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
        """
        Remove the One List account manager and tier from a company if it is an international
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
        methods=['patch'],
        permission_classes=[
            HasPermissions(
                f'company.{CompanyPermission.change_company}',
                f'company.change_companyexportcountry',
            ),
        ],
        detail=True,
    )
    def update_export_detail(self, request, *args, **kwargs):
        """
        Update export related information for the company.
        """
        instance = self.get_object()
        serializer = UpdateExportDetailsSerializer(
            instance=instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


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
    """
    Views for the One List Core Team of the group a company is part of.
    A Core Team is usually assigned to the Global Headquarters and is shared among all
    members of the group.

    The permissions to access this resource are inherited from the company resource.

    E.g. user only needs `view_company` permission to GET this collection and
    onelistcoreteammember permissions are ignored for now.
    """

    required_scopes = (Scope.internal_front_end,)
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

    required_scopes = (Scope.internal_front_end,)
    queryset = Company.objects.all()


class ContactViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Contact ViewSet v3."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = ContactSerializer
    queryset = get_contact_queryset()
    filter_backends = (
        DjangoFilterBackend, OrderingFilter,
    )
    filterset_fields = ['company_id']
    ordering = ('-created_on',)

    def get_additional_data(self, create):
        """Set adviser to the user on model instance creation."""
        data = super().get_additional_data(create)
        if create:
            data['adviser'] = self.request.user
        return data


class ContactAuditViewSet(AuditViewSet):
    """Contact audit views."""

    required_scopes = (Scope.internal_front_end,)
    queryset = Contact.objects.all()


class AdviserFilter(FilterSet):
    """Adviser filter."""

    autocomplete = AutocompleteFilter(
        search_fields=('first_name', 'last_name', 'dit_team__name'),
    )

    class Meta:
        model = Advisor
        fields = {
            'is_active': ('exact',),
        }


class AdviserReadOnlyViewSetV1(
        mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet,
):
    """Adviser GET only views."""

    required_scopes = (Scope.internal_front_end,)
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
    _default_ordering = ('first_name', 'last_name', 'dit_team__name')

    def filter_queryset(self, queryset):
        """
        Applies the default ordering when the query set has not already been ordered.

        (The autocomplete filter automatically applies an ordering, hence we only set the
        default ordering when another one has not already been set.)
        """
        filtered_queryset = super().filter_queryset(queryset)

        if not filtered_queryset.ordered:
            return filtered_queryset.order_by(*self._default_ordering)

        return filtered_queryset

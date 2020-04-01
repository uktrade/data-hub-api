"""Company and related resources view sets."""
from django.contrib.auth.models import Group, Permission
from django.db.models import Exists, Prefetch, Q
from django.http import Http404, JsonResponse
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.viewsets import GenericViewSet

from config.settings.types import HawkScope
from datahub.company.autocomplete import AutocompleteFilter
from datahub.company.company_matching_api import (
    CompanyMatchingServiceConnectionError,
    CompanyMatchingServiceHTTPError,
    CompanyMatchingServiceTimeoutError,
    match_company,
)
from datahub.company.export_wins_api import (
    export_wins,
    ExportWinsAPIConnectionError,
    ExportWinsAPIHTTPError,
    ExportWinsAPITimeoutError,
)
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
from datahub.core.exceptions import APIBadRequestException, APIUpstreamException
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.permissions import HasPermissions
from datahub.core.schemas import StubSchema
from datahub.core.view_utils import enforce_request_content_type
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


def _build_permission_filter(app_label, codename):
    """
    Create a Q object that checks if an adviser has a particular permission.

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
        """
        Filter advisers by a single permission (e.g. filter to advisers with the
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


class ExportWinsForCompanyView(RetrieveAPIView):
    """
    View returning export wins for a company, retrieved from Export Wins
    system, based on the match id obtained from Company Matching Service.
    """
    required_scopes = (Scope.internal_front_end,)
    queryset = Company.objects
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        HasPermissions(
            f'company.{CompanyPermission.view_export_win}',
        ),
    )

    def _extract_match_id(self, response):
        """
        Extracts match id out of company matching response
        {
            "matches": [
                {
                    "id": "",
                    "match_id": 1234,
                    "similarity": "100000"
                },
            ]
        }
        """
        return response.json()['matches'][0]['match_id']

    def _extract_export_wins(self, response):
        """
        Extracts export wins results out of export wins reponse
        {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": "c1428ed5-6154-4b17-aded-10a4c85a6431",
                    "date": "2016-05-25",
                    "created": "2020-02-18T15:36:02.782000Z",
                    "country": "CA",
                    "sector": 251,
                    "business_potential": 1,
                    "business_type": "",
                    "name_of_export": "food",
                    "officer": {
                        "name": "lead officer name",
                        "email": "",
                        "team": {
                            "type": "tcp",
                            "sub_type": "tcp:12"
                        }
                    },
                    "contact": {
                        "name": "customer name",
                        "email": "noname@commercialsoftware.co.uk",
                        "job_title": "customer job title"
                    },
                    "value": {
                        "export": {
                            "value": 100,
                            "breakdowns": [
                                {
                                    "year": 2021,
                                    "value": 100
                                }
                            ]
                        }
                    },
                    "customer": "Commercial Software Limited",
                    "response": null,
                    "hvc": {
                        "code": "E24116",
                        "name": "AER-01"
                    }
                },
            ]
        }
        """
        return response.json()

    def retrieve(self, request, *args, **kwargs):
        """
        Proxy to Export Wins API for GET requests for given company's match id
        is obtained from Company Matching Service
        """
        company = self.get_object()
        try:
            matching_response = match_company(company)
            match_id = self._extract_match_id(matching_response)
            if match_id:
                export_wins_reponse = export_wins(match_id)
                results = self._extract_export_wins(export_wins_reponse)
                return JsonResponse(results)
            raise Http404

        except (
            CompanyMatchingServiceConnectionError,
            CompanyMatchingServiceTimeoutError,
            ExportWinsAPIConnectionError,
            ExportWinsAPITimeoutError,
        ) as exc:
            raise APIUpstreamException(str(exc))

        except (ExportWinsAPIHTTPError, CompanyMatchingServiceHTTPError) as exc:
            raise APIBadRequestException(str(exc))

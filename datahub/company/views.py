"""Company and related resources view sets."""
from django.db.models import Prefetch
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from datahub.company.models import (
    Advisor,
    CompaniesHouseCompany,
    Company,
    Contact,
)
from datahub.company.queryset import get_contact_queryset
from datahub.company.serializers import (
    AdviserSerializer,
    CompaniesHouseCompanySerializer,
    CompanyCoreTeamMemberSerializer,
    CompanySerializer,
    ContactSerializer,
)
from datahub.core.audit import AuditViewSet
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.investment.queryset import get_slim_investment_project_queryset
from datahub.oauth.scopes import Scope


class CompanyViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Company view set V3."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = CompanySerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ('global_headquarters_id',)
    ordering_fields = ('name', 'created_on')
    queryset = Company.objects.select_related(
        'archived_by',
        'business_type',
        'classification',
        'employee_range',
        'export_experience_category',
        'headquarter_type',
        'one_list_account_owner',
        'global_headquarters',
        'registered_address_country',
        'trading_address_country',
        'turnover_range',
        'uk_region',
    ).prefetch_related(
        Prefetch('contacts', queryset=get_contact_queryset()),
        Prefetch('investor_investment_projects', queryset=get_slim_investment_project_queryset()),
        'export_to_countries',
        'future_interest_countries',
        'sector',
        'sector__parent',
        'sector__parent__parent',
    )


class CompanyCoreTeamViewSet(CoreViewSet):
    """
    Views for the core team of a company.

    The permissions to access this resource are inherited from the company resource.

    E.g. user only needs `view_company` permission to GET this collection and
    companycoreteam permissions are ignored for now.
    """

    required_scopes = (Scope.internal_front_end,)
    queryset = Company.objects.select_related(
        'one_list_account_owner',
        'one_list_account_owner__dit_team',
        'one_list_account_owner__dit_team__uk_region',
        'one_list_account_owner__dit_team__country',
    )
    serializer_class = CompanyCoreTeamMemberSerializer

    def list(self, request, *args, **kwargs):
        """Lists core team members."""
        company = self.get_object()
        global_account_manager = company.one_list_account_owner

        objs = []
        # add global account manager first
        if company.one_list_account_owner:
            objs.append(
                {
                    'adviser': global_account_manager,
                    'is_global_account_manager': True,
                },
            )

        # add all other core members excluding the global account manager
        # who might have already been added
        team_members = company.core_team_members.exclude(
            adviser=global_account_manager,
        ).select_related(
            'adviser',
            'adviser__dit_team',
            'adviser__dit_team__uk_region',
            'adviser__dit_team__country',
        ).order_by(
            'adviser__first_name',
            'adviser__last_name',
        )

        objs.extend(
            {
                'adviser': team_member.adviser,
                'is_global_account_manager': False,
            }
            for team_member in team_members
        )

        serializer = self.get_serializer(objs, many=True)
        return Response(serializer.data)


class CompanyAuditViewSet(AuditViewSet):
    """Company audit views."""

    required_scopes = (Scope.internal_front_end,)
    queryset = Company.objects.all()


class CompaniesHouseCompanyViewSet(
        mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet,
):
    """Companies House company read-only GET only views."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = CompaniesHouseCompanySerializer
    queryset = CompaniesHouseCompany.objects.select_related('registered_address_country').all()
    lookup_field = 'company_number'


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

    class Meta:
        model = Advisor
        fields = dict(
            first_name=['exact', 'icontains'],
            last_name=['exact', 'icontains'],
            email=['exact', 'icontains'],
        )


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
    ordering_fields = ('first_name', 'last_name')
    ordering = ('first_name', 'last_name')

"""Company and related resources view sets."""
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
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
    CompaniesHouseCompanySerializerV3,
    CompanySerializerV3,
    CompanySerializerV4,
    ContactSerializer,
    OneListCoreTeamMemberSerializer,
)
from datahub.company.validators import NotATransferredCompanyValidator
from datahub.core.audit import AuditViewSet
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.investment.queryset import get_slim_investment_project_queryset
from datahub.oauth.scopes import Scope


class BaseCompanyViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Base Company view set."""

    required_scopes = (Scope.internal_front_end,)
    unarchive_validators = (NotATransferredCompanyValidator(),)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ('global_headquarters_id',)
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
        'trading_address_country',
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
    )


class CompanyViewSetV3(BaseCompanyViewSet):
    """
    Company view set V3.

    TODO: delete once the migration to address and registered address is complete
    """

    serializer_class = CompanySerializerV3


class CompanyViewSetV4(BaseCompanyViewSet):
    """Company view set V4."""

    serializer_class = CompanySerializerV4


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


class CompaniesHouseCompanyViewSetV3(
        mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet,
):
    """Companies House company read-only GET only views V3."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = CompaniesHouseCompanySerializerV3
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
        fields = {
            'first_name': ('exact', 'icontains'),
            'last_name': ('exact', 'icontains'),
            'email': ('exact', 'icontains'),
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
    ordering_fields = ('first_name', 'last_name')
    ordering = ('first_name', 'last_name')

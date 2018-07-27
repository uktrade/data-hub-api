"""Company and related resources view sets."""
from django.db.models import Prefetch
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from datahub.core.audit import AuditViewSet
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSet
from datahub.investment.queryset import get_slim_investment_project_queryset
from datahub.oauth.scopes import Scope
from .models import (
    Advisor,
    CompaniesHouseCompany,
    Company,
    Contact,
)
from .queryset import get_contact_queryset
from .serializers import (
    AdviserSerializer,
    CompaniesHouseCompanySerializer,
    CompanyCoreTeamMemberSerializer,
    CompanySerializer,
    ContactSerializer,
)


class CompanyViewSet(ArchivableViewSetMixin, CoreViewSet):
    """Company view set V3."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = CompanySerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ('global_headquarters_id',)
    ordering_fields = ('name', 'created_on')
    queryset = Company.objects.select_related(
        'account_manager',
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

    When a company is account managed, a core team is established.
    This usually includes:
    - one and only one global account manager
    - a local account manager from the country where the company is based
    - one or more local account managers from the country where the company
        is exporting to or investing in

    However, this layout is not always as strict.
    Other roles might exist and an single person can also have multiple roles.

    This team is called "core team" because it's official and does not change
    often. Usually, a wider team around a company is established as well.
    This team includes specialists and other advisers needed for short-term
    and more reactive support.


    At the moment, this endpoint only includes company.one_list_account_owner
    representing the global account manager.
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
        objs = []
        if company.one_list_account_owner:
            objs.append(
                {
                    'adviser': company.one_list_account_owner,
                    'is_global_account_manager': True
                }
            )

        serializer = self.get_serializer(objs, many=True)
        return Response(serializer.data)


class CompanyAuditViewSet(AuditViewSet):
    """Company audit views."""

    required_scopes = (Scope.internal_front_end,)
    queryset = Company.objects.all()


class CompaniesHouseCompanyViewSet(
        mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
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
        DjangoFilterBackend, OrderingFilter
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
        mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
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

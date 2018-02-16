"""Company and related resources view sets."""
from django.db.models import Prefetch
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter

from datahub.core.audit import AuditViewSet
from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSetV3
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
    CompanySerializer,
    ContactSerializer,
)


class CompanyViewSet(ArchivableViewSetMixin, CoreViewSetV3):
    """Company view set V3."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = CompanySerializer
    queryset = Company.objects.select_related(
        'account_manager',
        'archived_by',
        'business_type',
        'classification',
        'employee_range',
        'export_experience_category',
        'headquarter_type',
        'one_list_account_owner',
        'parent',
        'global_headquarters',
        'registered_address_country',
        'sector',
        'trading_address_country',
        'turnover_range',
        'uk_region',
    ).prefetch_related(
        Prefetch('contacts', queryset=get_contact_queryset()),
        Prefetch('investor_investment_projects', queryset=get_slim_investment_project_queryset()),
        'children',
        'subsidiaries',
        'export_to_countries',
        'future_interest_countries',
    )


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


class ContactViewSet(ArchivableViewSetMixin, CoreViewSetV3):
    """Contact ViewSet v3."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = ContactSerializer
    queryset = get_contact_queryset()
    filter_backends = (
        DjangoFilterBackend, OrderingFilter
    )
    filter_fields = ['company_id']
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
    filter_class = AdviserFilter
    ordering_fields = ('first_name', 'last_name')
    ordering = ('first_name', 'last_name')

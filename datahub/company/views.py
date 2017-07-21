"""Company and related resources view sets."""
from django.db.models import Prefetch
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.serializers import AuditSerializer
from datahub.core.viewsets import CoreViewSetV1, CoreViewSetV3
from datahub.investment.models import InvestmentProject
from .models import Advisor, CompaniesHouseCompany, Company, Contact
from .serializers import (
    AdviserSerializer, CompaniesHouseCompanySerializer,
    CompanySerializerReadV1, CompanySerializerV3, CompanySerializerWriteV1,
    ContactSerializer
)


def _get_contact_queryset():
    return Contact.objects.select_related(
        'title',
        'company',
        'adviser',
        'address_country',
        'archived_by'
    )


def _get_slim_investment_project_queryset():
    return InvestmentProject.objects.select_related(
        'investmentprojectcode',
    )


class CompanyViewSetV1(ArchivableViewSetMixin, CoreViewSetV1):
    """Company ViewSet."""

    read_serializer_class = CompanySerializerReadV1
    write_serializer_class = CompanySerializerWriteV1
    queryset = Company.objects.select_related(
        'business_type',
        'sector',
        'archived_by',
        'registered_address_country',
        'trading_address_country',
        'employee_range',
        'turnover_range',
        'account_manager'
    ).prefetch_related(
        'contacts',
        'interactions',
        'export_to_countries',
        'future_interest_countries'
    )


class CompanyViewSetV3(ArchivableViewSetMixin, CoreViewSetV3):
    """Company view set V3."""

    serializer_class = CompanySerializerV3
    queryset = Company.objects.select_related(
        'account_manager',
        'archived_by',
        'business_type',
        'classification',
        'employee_range',
        'headquarter_type',
        'one_list_account_owner',
        'parent',
        'registered_address_country',
        'sector',
        'trading_address_country',
        'turnover_range',
        'uk_region',
    ).prefetch_related(
        Prefetch('contacts', queryset=_get_contact_queryset()),
        Prefetch('investor_investment_projects',
                 queryset=InvestmentProject.objects.select_related('investmentprojectcode')),
        'children',
        'export_to_countries',
        'future_interest_countries',
    )


class CompanyAuditViewSet(CoreViewSetV3):
    """Company audit views."""

    serializer_class = AuditSerializer
    queryset = Company.objects.all()


class CompaniesHouseCompanyReadOnlyViewSetV1(
        mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Companies House company GET only views."""

    serializer_class = CompaniesHouseCompanySerializer
    queryset = CompaniesHouseCompany.objects.select_related('registered_address_country').all()
    lookup_field = 'company_number'


class ContactViewSet(ArchivableViewSetMixin, CoreViewSetV3):
    """Contact ViewSet v3."""

    serializer_class = ContactSerializer
    queryset = _get_contact_queryset()
    filter_backends = (
        DjangoFilterBackend,
    )
    filter_fields = ['company_id']

    def get_additional_data(self, create):
        """Set adviser to the user on model instance creation."""
        data = {}
        if create:
            data['adviser'] = self.request.user
        return data


class ContactAuditViewSet(CoreViewSetV3):
    """Contact audit views."""

    serializer_class = AuditSerializer
    queryset = Contact.objects.all()


class AdviserFilter(FilterSet):
    """Adviser filter."""

    class Meta:  # noqa: D101
        model = Advisor
        fields = dict(
            first_name=['exact', 'icontains'],
            last_name=['exact', 'icontains'],
            email=['exact', 'icontains'],
        )


class AdviserReadOnlyViewSetV1(
        mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Adviser GET only views."""

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

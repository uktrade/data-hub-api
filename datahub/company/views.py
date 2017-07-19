"""Company and related resources view sets."""
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.serializers import AuditSerializer
from datahub.core.viewsets import CoreViewSetV1, CoreViewSetV3
from .models import Advisor, CompaniesHouseCompany, Company, Contact
from .serializers import (
    AdviserSerializer, CompaniesHouseCompanySerializer,
    CompanySerializerReadV1, CompanySerializerV3, CompanySerializerWriteV1,
    ContactSerializer
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
        'archived_by',
        'registered_address_country',
        'trading_address_country',
        'account_manager',
        'business_type',
        'classification',
        'employee_range',
        'headquarter_type',
        'one_list_account_owner',
        'parent',
        'sector',
        'turnover_range',
        'uk_region',
    ).prefetch_related(
        'investor_investment_projects',
        'children',
        'contacts',
        'export_to_countries',
        'future_interest_countries'
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
    queryset = Contact.objects.select_related(
        'title',
        'company',
        'adviser',
        'address_country',
        'archived_by'
    )
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
    queryset = Advisor.objects.all()
    filter_backends = (
        DjangoFilterBackend,
    )
    filter_class = AdviserFilter

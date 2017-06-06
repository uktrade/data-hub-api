"""Company and related resources view sets."""
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSetV1, CoreViewSetV3
from .models import Advisor, CompaniesHouseCompany, Company, Contact
from .serializers import (
    AdviserSerializer, CompaniesHouseCompanySerializer, CompanySerializerRead,
    CompanySerializerWrite, ContactSerializer
)


class CompanyViewSetV1(ArchivableViewSetMixin, CoreViewSetV1):
    """Company ViewSet."""

    read_serializer_class = CompanySerializerRead
    write_serializer_class = CompanySerializerWrite
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


class CompaniesHouseCompanyReadOnlyViewSetV1(
        mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Companies House company GET only views."""

    serializer_class = CompaniesHouseCompanySerializer
    queryset = CompaniesHouseCompany.objects.select_related('registered_address_country').all()
    lookup_field = 'company_number'


class ContactViewSet(ArchivableViewSetMixin, CoreViewSetV3):
    """Contact ViewSet v3."""

    read_serializer_class = ContactSerializer
    write_serializer_class = ContactSerializer
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

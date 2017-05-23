"""Company and related resources view sets."""
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSetV1, CoreViewSetV3
from .models import Advisor, CompaniesHouseCompany, Company, Contact
from .serializers import (
    AdvisorSerializer, CompaniesHouseCompanySerializer, CompanySerializerRead,
    CompanySerializerWrite, ContactSerializerV1Read, ContactSerializerV1Write,
    ContactSerializerV3
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


class ContactViewSetV1(ArchivableViewSetMixin, CoreViewSetV1):
    """Contact ViewSet."""

    read_serializer_class = ContactSerializerV1Read
    write_serializer_class = ContactSerializerV1Write
    queryset = Contact.objects.select_related(
        'title',
        'company',
        'address_country',
    ).prefetch_related(
        'teams',
        'interactions'
    )

    def get_additional_data(self, update):
        """Override create to inject the user from session."""
        data = super().get_additional_data(update)
        data['advisor'] = self.request.user
        return data


class ContactViewSetV3(ArchivableViewSetMixin, CoreViewSetV3):
    """Contact ViewSet v3."""

    read_serializer_class = ContactSerializerV3
    write_serializer_class = ContactSerializerV3
    queryset = Contact.objects.select_related(
        'title',
        'company',
        'advisor',
        'address_country',
        'archived_by'
    )
    filter_backends = (
        DjangoFilterBackend,
    )
    filter_fields = ['company_id']

    def perform_create(self, serializer):
        """Override create to inject the user from session."""
        request = serializer.context['request']
        serializer.save(advisor=request.user)


class AdvisorFilter(FilterSet):
    """Advisor filter."""

    class Meta:  # noqa: D101
        model = Advisor
        fields = dict(
            first_name=['exact', 'icontains'],
            last_name=['exact', 'icontains'],
            email=['exact', 'icontains'],
        )


class AdvisorReadOnlyViewSetV1(
        mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Advisor GET only views."""

    serializer_class = AdvisorSerializer
    queryset = Advisor.objects.all()
    filter_backends = (
        DjangoFilterBackend,
    )
    filter_class = AdvisorFilter

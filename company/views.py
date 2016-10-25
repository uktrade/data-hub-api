"""Company and related resources view sets."""

from rest_framework import mixins, viewsets

from core.viewsets import ArchiveNoDeleteViewSet
from .models import Company, CompaniesHouseCompany, Contact, Interaction, Advisor
from .serializers import (CompanySerializerRead, CompanySerializerWrite,
                          CompaniesHouseCompanySerializer,
                          ContactSerializerRead, ContactSerializerWrite,
                          InteractionSerializerRead, InteractionSerializerWrite, AdvisorSerializer)


class CompanyViewSet(ArchiveNoDeleteViewSet):
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
    ).exclude(name='Undefined')


class CompaniesHouseCompanyReadOnlyViewSet(mixins.ListModelMixin,
                                           mixins.RetrieveModelMixin,
                                           viewsets.GenericViewSet):
    """Companies House company GET only views."""

    serializer_class = CompaniesHouseCompanySerializer
    queryset = CompaniesHouseCompany.objects.select_related('registered_address_country').all()
    lookup_field = 'company_number'


class ContactViewSet(ArchiveNoDeleteViewSet):
    """Contact ViewSet."""

    read_serializer_class = ContactSerializerRead
    write_serializer_class = ContactSerializerWrite
    queryset = Contact.objects.select_related(
        'title',
        'role',
        'company',
        'address_country',
        'uk_region'
    ).prefetch_related(
        'teams'
    ).exclude(name='Undefined')


class InteractionViewSet(ArchiveNoDeleteViewSet):
    """Interaction ViewSet."""

    read_serializer_class = InteractionSerializerRead
    write_serializer_class = InteractionSerializerWrite
    queryset = Interaction.objects.select_related(
        'interaction_type',
        'advisor',
        'company',
        'contact'
    ).exclude(name='Undefined')


class AdvisorReadOnlyViewSet(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    """Advisor GET only views."""

    serializer_class = AdvisorSerializer
    queryset = Advisor.objects..exclude(name='Undefined')

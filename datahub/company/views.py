"""Company and related resources view sets."""

from rest_framework import mixins, viewsets

from datahub.core.viewsets import CoreViewSet
from .models import Advisor, CompaniesHouseCompany, Company, Contact, Interaction
from .serializers import (AdvisorSerializer, CompaniesHouseCompanySerializer, CompanySerializerRead,
                          CompanySerializerWrite, ContactSerializerRead, ContactSerializerWrite,
                          InteractionSerializerRead, InteractionSerializerWrite)


class CompanyViewSet(CoreViewSet):
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


class ContactViewSet(CoreViewSet):
    """Contact ViewSet."""

    read_serializer_class = ContactSerializerRead
    write_serializer_class = ContactSerializerWrite
    queryset = Contact.objects.select_related(
        'title',
        'role',
        'company',
        'address_country',
    ).prefetch_related(
        'teams',
        'interactions'
    ).exclude(first_name='Undefined')

    def create(self, request, *args, **kwargs):
        """Override create to inject the user from session."""
        request.data.update({'advisor': str(request.user.pk)})
        return super().create(request, *args, **kwargs)


class InteractionViewSet(CoreViewSet):
    """Interaction ViewSet."""

    read_serializer_class = InteractionSerializerRead
    write_serializer_class = InteractionSerializerWrite
    queryset = Interaction.objects.select_related(
        'interaction_type',
        'dit_advisor',
        'company',
        'contact'
    ).all()

    def create(self, request, *args, **kwargs):
        """Override create to inject the user from session."""
        request.data.update({'dit_advisor': str(request.user.pk)})
        return super().create(request, *args, **kwargs)


class AdvisorReadOnlyViewSet(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    """Advisor GET only views."""

    serializer_class = AdvisorSerializer
    queryset = Advisor.objects.exclude(first_name='Undefined')

"""Company and related resources view sets."""

from rest_framework import mixins, viewsets

from core.viewsets import ArchiveNoDeleteViewSet
from .models import Company, CompaniesHouseCompany, Contact, Interaction
from .serializers import (CompanySerializerRead, CompanySerializerWrite,
                          CompaniesHouseCompanySerializer,
                          ContactSerializerRead, ContactSerializerWrite,
                          InteractionSerializerRead, InteractionSerializerWrite)


class CompanyViewSet(ArchiveNoDeleteViewSet):
    """Company ViewSet."""

    read_serializer_class = CompanySerializerRead
    write_serializer_class = CompanySerializerWrite
    queryset = Company.objects.select_related(
        'business_type',
        'sector',
        'country',
        'employee_range',
        'turnover_range',
        'uk_region'
    ).prefetch_related(
        'contacts',
        'interactions'
    ).all()


class CompaniesHouseCompanyReadOnlyViewSet(mixins.ListModelMixin,
                                           mixins.RetrieveModelMixin,
                                           viewsets.GenericViewSet):
    """Companies House company GET only views."""

    serializer_class = CompaniesHouseCompanySerializer
    queryset = CompaniesHouseCompany.objects.all()
    lookup_field = 'company_number'


class ContactViewSet(ArchiveNoDeleteViewSet):
    """Contact ViewSet."""

    read_serializer_class = ContactSerializerRead
    write_serializer_class = ContactSerializerWrite
    queryset = Contact.objects.select_related(
        'title',
        'role',
        'company'
    ).all()


class InteractionViewSet(ArchiveNoDeleteViewSet):
    """Interaction ViewSet."""

    read_serializer_class = InteractionSerializerRead
    write_serializer_class = InteractionSerializerWrite
    queryset = Interaction.objects.select_related(
        'interaction_type',
        'advisor',
        'company',
        'contact'
    ).all()

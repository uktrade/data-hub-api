"""Company and related resources view sets."""

from rest_framework import mixins, viewsets

from core.viewsets import ArchiveNoDeleteViewSet
from .models import Company, CompaniesHouseCompany, Contact, Interaction
from .serializers import CompanySerializer, CompaniesHouseCompanySerializer, ContactSerializer, InteractionSerializer


class CompanyViewSet(ArchiveNoDeleteViewSet):
    """Company ViewSet."""

    serializer_class = CompanySerializer
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


class ContactViewSet(ArchiveNoDeleteViewSet):
    """Contact ViewSet."""

    serializer_class = ContactSerializer
    queryset = Contact.objects.select_related(
        'title',
        'role',
        'company'
    ).all()


class InteractionViewSet(ArchiveNoDeleteViewSet):
    """Interaction ViewSet."""

    serializer_class = InteractionSerializer
    queryset = Interaction.objects.select_related(
        'interaction_type',
        'advisor',
        'company',
        'contact'
    ).all()

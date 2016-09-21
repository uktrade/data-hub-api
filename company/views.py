"""Company and related resources view sets."""

from core.viewsets import ArchiveNoDeleteViewSet
from .models import Company, Contact, Interaction
from .serializers import CompanySerializer, ContactSerializer, InteractionSerializer


class CompanyViewSet(ArchiveNoDeleteViewSet):
    """Company ViewSet."""

    serializer_class = CompanySerializer
    queryset = Company.objects.all()


class ContactViewSet(ArchiveNoDeleteViewSet):
    """Contact ViewSet."""

    serializer_class = ContactSerializer
    queryset = Contact.objects.all()


class InteractionViewSet(ArchiveNoDeleteViewSet):
    """Interaction ViewSet."""

    serializer_class = InteractionSerializer
    queryset = Interaction.objects.all()

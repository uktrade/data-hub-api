from rest_framework import viewsets
from api.models.chcompany import CHCompany
from api.serializers.chcompanyserializer import CHCompanySerializer


class CHCompanyViewSet(viewsets.ModelViewSet):
    """DBMS Company."""

    queryset = CHCompany.objects.all()
    serializer_class = CHCompanySerializer

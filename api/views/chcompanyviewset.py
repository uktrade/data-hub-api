from rest_framework import viewsets

from api.models.chcompany import CHCompany
from api.serializers import CHCompanySerializer


class CHCompanyViewSet(viewsets.ModelViewSet):
    queryset = CHCompany.objects.all()
    serializer_class = CHCompanySerializer

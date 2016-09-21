from rest_framework import viewsets

from .models import Company
from .serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """Company ViewSet."""

    serializer_class = CompanySerializer
    queryset = Company.objects.all()
    http_method_names = ('get', 'post', 'put', 'patch')

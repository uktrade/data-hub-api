from rest_framework import viewsets
from rest_framework import status
from api.models.company import Company
from api.models.searchitem import search_item_from_company
from api.serializers import CompanySerializer
from rest_framework.response import Response


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def create(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_company = serializer.save()
        search_item = search_item_from_company(new_company)
        search_item.add()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

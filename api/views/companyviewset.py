from rest_framework import status, viewsets
from rest_framework.response import Response

from api.models.chcompany import CHCompany
from api.models.company import Company
from api.serializers import CompanySerializer, CHCompanySerializer
# from korben.client import esclient


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def create(self, request, **kwargs):
        # eslient.check_ch_data(request)

        # Create a company, validate and save
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_company = serializer.save()

        # esclient.create(new_company)

        # send back the newly company record and inform the user if all is well.
        response_serializer = self.get_serializer(new_company)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # esclient.check_ch_data(request)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        # esclient.create(new_company)

        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        data = serializer.data

        # if there is a company_number, get the CH data and add that
        if instance.company_number and len(instance.company_number) > 0:
            ch_company = CHCompany.objects.get(pk=instance.company_number)
            ch_serializer = CHCompanySerializer(ch_company)
            data['ch'] = ch_serializer.data

        return Response(data)

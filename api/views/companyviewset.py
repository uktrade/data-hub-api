from rest_framework import viewsets, status
from rest_framework.response import Response
from api.models.chcompany import CHCompany
from api.models.company import Company
from api.serializers import CHCompanySerializer
from api.serializers import CompanySerializer
from api.services.searchservice import delete_for_company_number, delete_for_source_id, search_item_from_company


def check_ch_data(request):
    # look at the incoming data. Is there a company number?
    # if so then lookup some CH data and add it here before turning it
    # into a company.
    if request.data['company_number'] and len(request.data['company_number']) > 0:
        ch = CHCompany.objects.get(pk=request.data['company_number'])
        request.data['registered_name'] = ch.company_name
        request.data['business_type'] = ch.company_category


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def create(self, request, **kwargs):
        check_ch_data(request)

        # Create a company, validate and save
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_company = serializer.save()

        # Delete the existing index entry and create a new one.
        if request.data['company_number'] and len(request.data['company_number']) > 0:
            delete_for_company_number(new_company.company_number)

        search_item = search_item_from_company(new_company)
        search_item.save()

        # send back the newly company record and inform the user if all is well.
        response_serializer = self.get_serializer(new_company)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        check_ch_data(request)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        delete_for_source_id(company.id)
        search_item = search_item_from_company(company)
        search_item.save()

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

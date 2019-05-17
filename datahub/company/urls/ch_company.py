from django.urls import path

from datahub.company.views import CompaniesHouseCompanyViewSet


ch_company_collection = CompaniesHouseCompanyViewSet.as_view({
    'get': 'list',
})

ch_company_item = CompaniesHouseCompanyViewSet.as_view({
    'get': 'retrieve',
})

urls = [
    path('ch-company', ch_company_collection, name='collection'),
    path('ch-company/<company_number>', ch_company_item, name='item'),
]

from django.urls import path

from datahub.company.views import CompaniesHouseCompanyViewSetV3, CompaniesHouseCompanyViewSetV4

# TODO: delete once the migration to v4 is complete
ch_company_collection_v3 = CompaniesHouseCompanyViewSetV3.as_view({
    'get': 'list',
})

# TODO: delete once the migration to v4 is complete
ch_company_item_v3 = CompaniesHouseCompanyViewSetV3.as_view({
    'get': 'retrieve',
})

ch_company_collection_v4 = CompaniesHouseCompanyViewSetV4.as_view({
    'get': 'list',
})

ch_company_item_v4 = CompaniesHouseCompanyViewSetV4.as_view({
    'get': 'retrieve',
})

urls_v3 = [
    path('ch-company', ch_company_collection_v3, name='collection'),
    path('ch-company/<company_number>', ch_company_item_v3, name='item'),
]

urls_v4 = [
    path('ch-company', ch_company_collection_v4, name='collection'),
    path('ch-company/<company_number>', ch_company_item_v4, name='item'),
]

from django.urls import path

from datahub.company.views import (
    CompanyAuditViewSet,
    CompanyViewSet,
    OneListGroupCoreTeamViewSet,
    PublicCompanyViewSet,
)


company_collection = CompanyViewSet.as_view({
    'get': 'list',
})

company_item = CompanyViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})

company_audit = CompanyAuditViewSet.as_view({
    'get': 'list',
})

company_archive = CompanyViewSet.as_action_view('archive')

company_unarchive = CompanyViewSet.as_action_view('unarchive')

company_self_assign_account_manager = CompanyViewSet.as_action_view(
    'self_assign_account_manager',
)

company_remove_account_manager = CompanyViewSet.as_action_view(
    'remove_account_manager',
)

update_export_detail = CompanyViewSet.as_action_view(
    'update_export_detail',
)

one_list_group_core_team = OneListGroupCoreTeamViewSet.as_view({
    'get': 'list',
})

public_company_item = PublicCompanyViewSet.as_view({
    'get': 'retrieve',
})

urls = [
    path('company', company_collection, name='collection'),
    path('company/<uuid:pk>', company_item, name='item'),
    path('company/<uuid:pk>/archive', company_archive, name='archive'),
    path('company/<uuid:pk>/unarchive', company_unarchive, name='unarchive'),
    path('company/<uuid:pk>/audit', company_audit, name='audit-item'),
    path(
        'company/<uuid:pk>/self-assign-account-manager',
        company_self_assign_account_manager,
        name='self-assign-account-manager',
    ),
    path(
        'company/<uuid:pk>/remove-account-manager',
        company_remove_account_manager,
        name='remove-account-manager',
    ),
    path(
        'company/<uuid:pk>/one-list-group-core-team',
        one_list_group_core_team,
        name='one-list-group-core-team',
    ),
    path(
        'company/<uuid:pk>/export-detail',
        update_export_detail,
        name='update-export-detail',
    ),
    path('public/company/<uuid:pk>', public_company_item, name='public-item'),
]

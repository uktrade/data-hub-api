from django.urls import path

from datahub.company.views import (
    CompanyAuditViewSet,
    CompanyViewSet,
    ExportWinsForCompanyView,
    OneListGroupCoreTeamViewSet,
    PublicCompanyViewSet,
)

company_collection = CompanyViewSet.as_view(
    {
        'get': 'list',
        'post': 'create',
    },
)

company_item = CompanyViewSet.as_view(
    {
        'get': 'retrieve',
        'patch': 'partial_update',
    },
)

company_audit = CompanyAuditViewSet.as_view(
    {
        'get': 'list',
    },
)

company_archive = CompanyViewSet.as_action_view('archive')

company_unarchive = CompanyViewSet.as_action_view('unarchive')

company_assign_regional_account_manager = CompanyViewSet.as_action_view(
    'assign_regional_account_manager',
)

company_self_assign_account_manager = CompanyViewSet.as_action_view(
    'self_assign_account_manager',
)

company_remove_account_manager = CompanyViewSet.as_action_view(
    'remove_account_manager',
)

company_assign_one_list_tier_and_global_account_manager = CompanyViewSet.as_action_view(
    'assign_one_list_tier_and_global_account_manager',
)

company_remove_from_one_list = CompanyViewSet.as_action_view('remove_from_one_list')

update_export_detail = CompanyViewSet.as_action_view(
    'update_export_detail',
)

kings_awards_list = CompanyViewSet.as_action_view('kings_awards')

one_list_group_core_team = OneListGroupCoreTeamViewSet.as_view(
    {
        'get': 'list',
    },
)

update_one_list_core_team = CompanyViewSet.as_action_view(
    'update_one_list_core_team',
)

public_company_item = PublicCompanyViewSet.as_view(
    {
        'get': 'retrieve',
    },
)

urls = [
    path('company', company_collection, name='collection'),
    path('company/<uuid:pk>', company_item, name='item'),
    path('company/<uuid:pk>/archive', company_archive, name='archive'),
    path('company/<uuid:pk>/unarchive', company_unarchive, name='unarchive'),
    path('company/<uuid:pk>/audit', company_audit, name='audit-item'),
    path(
        'company/<uuid:pk>/assign-regional-account-manager',
        company_assign_regional_account_manager,
        name='assign-regional-account-manager',
    ),
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
        'company/<uuid:pk>/assign-one-list-tier-and-global-account-manager',
        company_assign_one_list_tier_and_global_account_manager,
        name='assign-one-list-tier-and-global-account-manager',
    ),
    path(
        'company/<uuid:pk>/remove-from-one-list',
        company_remove_from_one_list,
        name='remove-from-one-list',
    ),
    path(
        'company/<uuid:pk>/one-list-group-core-team',
        one_list_group_core_team,
        name='one-list-group-core-team',
    ),
    path(
        'company/<uuid:pk>/update-one-list-core-team',
        update_one_list_core_team,
        name='update-one-list-core-team',
    ),
    path(
        'company/<uuid:pk>/export-detail',
        update_export_detail,
        name='update-export-detail',
    ),
    path(
        'company/<uuid:pk>/export-win',
        ExportWinsForCompanyView.as_view(),
        name='export-win',
    ),
    path(
        'company/<uuid:pk>/kings-awards',
        kings_awards_list,
        name='kings-awards-list',
    ),
    path('public/company/<uuid:pk>', public_company_item, name='public-item'),
]

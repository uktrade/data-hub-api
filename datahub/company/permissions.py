from rest_framework.permissions import BasePermission

from datahub.company.models import CompanyPermission


class IsAccountManagerOnCompany(BasePermission):
    """
    Allows users:
    - that have change_company and change_one_list_tier_and_global_account_manager permissions
    - or that are one_list_account_owners (account managers/ITA Leads) for the current record.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.has_perms([
            f'company.{CompanyPermission.change_company}',
            f'company.{CompanyPermission.change_one_list_tier_and_global_account_manager}',
        ]) or (obj.one_list_account_owner == request.user)

from rest_framework.permissions import BasePermission

from datahub.company.models import CompanyPermission


class IsAccountManagerOnCompany(BasePermission):
    """Allows users:
    - that have change_company permission and are one_list_account_owners (account managers/ITA
      Leads) for the current record.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.has_perms(
            [
                f'company.{CompanyPermission.change_company}',
            ],
        ) and (obj.one_list_account_owner == request.user)

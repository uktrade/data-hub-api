from django.shortcuts import get_object_or_404
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.company.models import Company, CompanyPermission
from datahub.oauth.scopes import Scope
from datahub.user.company_list.models import CompanyListItem, CompanyListItemPermissionCode


class CompanyListItemPermissions(DjangoModelPermissions):
    """DRF permissions class for the company list item view."""

    perms_map = {
        'DELETE': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermissionCode.delete_company_list_item}',
        ],
        'PUT': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermissionCode.add_company_list_item}',
        ],
    }


class CompanyListItemView(APIView):
    """
    View for adding and removing a company to and from a user's list of companies.

    This does not use CoreViewSet at present as the desired behaviour is slightly
    different due to the simple nature of the functionality (which is effectively
    starring and unstarring a company).

    However, if the functionality becomes more complicated (e.g. multiple lists per user)
    switching to CoreViewSet would probably make sense.
    """

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        CompanyListItemPermissions,
    )
    # Note: A query set is required for CompanyListItemPermissions
    queryset = CompanyListItem.objects.all()

    def put(self, request, format=None, company_pk=None):
        """
        Create a CompanyListItem for the authenticated user and specified company
        if it doesn't already exist.

        Note that this attempts to behave the same even if whether the company was
        added on the user's list.
        """
        company = get_object_or_404(Company, pk=company_pk)

        # update_or_create() is used to avoid an error if there is an existing
        # CompanyListItem for this adviser and company
        self.queryset.update_or_create(
            defaults={
                'adviser': request.user,
                'company': company,
            },
        )

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, format=None, company_pk=None):
        """
        Delete a CompanyListItem for the authenticated user and specified company
        if it exists.

        Note that this attempts to behave the same regardless of whether the company was
        on the user's list.
        """
        company = get_object_or_404(Company, pk=company_pk)

        self.queryset.filter(
            adviser=request.user,
            company=company,
        ).delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

from django.http import Http404
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.company.models import Company, CompanyPermission
from datahub.core.permissions import HasPermissions
from datahub.oauth.scopes import Scope
from datahub.user.company_list.models import CompanyListItemPermission
from datahub.user.company_list.serializers import CompanyListItemSerializer


class CreateOrUpdateCompanyListItemView(APIView):
    """View for adding a company to a user's list of companies."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermission.add_company_list_item}',
        ),
    )

    def put(self, request, format=None, company_pk=None):
        """
        Create a CompanyListItem for the authenticated user and specified company
        if it doesn't already exist.
        """
        if not Company.objects.filter(pk=company_pk).exists():
            raise Http404()

        data = {
            'adviser': request.user.pk,
            'company': company_pk,
        }
        serializer = CompanyListItemSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update_or_create()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

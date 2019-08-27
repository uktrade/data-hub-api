from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import serializers, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from datahub.company.models import Company, CompanyPermission
from datahub.core.viewsets import CoreViewSet
from datahub.oauth.scopes import Scope
from datahub.user.company_list.models import (
    CompanyList,
    CompanyListItem,
    CompanyListItemPermissionCode,
)
from datahub.user.company_list.queryset import get_company_list_item_queryset
from datahub.user.company_list.serializers import CompanyListItemSerializer

CANT_ADD_ARCHIVED_COMPANY_MESSAGE = gettext_lazy(
    "An archived company can't be added to a company list.",
)


class CompanyListItemPermissions(DjangoModelPermissions):
    """DRF permissions class for the company list item view."""

    perms_map = {
        'DELETE': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermissionCode.delete_company_list_item}',
        ],
        'GET': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermissionCode.view_company_list_item}',
        ],
        'HEAD': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermissionCode.view_company_list_item}',
        ],
        'PUT': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermissionCode.add_company_list_item}',
        ],
    }


class CompanyListItemAPIView(APIView):
    """
    A view for adding and removing a company to and from a selected list of companies
    that belongs to a user.
    """

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        CompanyListItemPermissions,
    )
    # Note: A query set is required for CompanyListItemPermissions
    queryset = CompanyListItem.objects.all()
    serializer_class = CompanyListItemSerializer

    @method_decorator(transaction.non_atomic_requests)
    def put(self, request, company_list_pk, company_pk, format=None):
        """Add company to a list."""
        company = get_object_or_404(Company, pk=company_pk)
        if company.archived:
            errors = {
                api_settings.NON_FIELD_ERRORS_KEY: CANT_ADD_ARCHIVED_COMPANY_MESSAGE,
            }
            raise serializers.ValidationError(errors)

        adviser = request.user
        company_list = self._get_company_list(request, company_list_pk)

        # get_or_create() is used to avoid an error if there is an existing
        # CompanyListItem for this adviser and company
        self.queryset.get_or_create(
            company=company,
            list=company_list,
            defaults={
                'created_by': adviser,
                'modified_by': adviser,
            },
        )

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def _get_company_list(self, request, company_list_pk):
        obj = get_object_or_404(
            CompanyList,
            adviser=request.user,
            pk=company_list_pk,
        )
        self.check_object_permissions(request, obj)
        return obj


class CompanyListItemViewSet(CoreViewSet):
    """A view set for returning the contents of a company list."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        CompanyListItemPermissions,
    )
    serializer_class = CompanyListItemSerializer
    filter_backends = (OrderingFilter,)
    # Note that we want null to be treated as the oldest value when sorting by
    # how long ago the interaction happened. This happens automatically when sorting by
    # latest_interaction_time_ago (as opposed to sorting by latest_interaction_date in
    # descending order)
    ordering = (
        'latest_interaction_time_ago',
        '-latest_interaction_created_on',
        'latest_interaction_id',
    )
    queryset = get_company_list_item_queryset()

    def initial(self, request, *args, **kwargs):
        """
        Raise an Http404 if company list specified in the URL path does not exist.
        """
        super().initial(request, *args, **kwargs)

        if not CompanyList.objects.filter(pk=self.kwargs['company_list_pk']).exists():
            raise Http404

    def filter_queryset(self, queryset):
        """Filter the query set to the items relating to the authenticated users."""
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            list__adviser=self.request.user,
            list__pk=self.request.parser_context['kwargs']['company_list_pk'],
        )

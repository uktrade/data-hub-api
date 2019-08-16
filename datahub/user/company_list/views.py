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

DEFAULT_LEGACY_LIST_NAME = '1. My list'


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


class CompanyListViewSet(CoreViewSet):
    """
    View set for returning the contents of a company list.

    Note that CompanyListItemView is used for operations relating to a single item.
    """

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

    def filter_queryset(self, queryset):
        """Filter the query set to the items relating to the authenticated users."""
        queryset = super().filter_queryset(queryset)
        return queryset.filter(adviser=self.request.user)


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

    def get(self, request, format=None, company_pk=None):
        """Check if a CompanyListItem exists for the authenticated user and specified company."""
        company_exists = CompanyListItem.objects.filter(
            adviser=request.user.pk,
            company_id=company_pk,
        ).exists()

        if not company_exists:
            raise Http404()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @method_decorator(transaction.non_atomic_requests)
    def put(self, request, format=None, company_pk=None):
        """
        Create a CompanyListItem for the authenticated user and specified company
        if it doesn't already exist.

        Note that this attempts to behave the same even if whether the company was
        added on the user's list.
        """
        company = get_object_or_404(Company, pk=company_pk)

        if company.archived:
            errors = {
                api_settings.NON_FIELD_ERRORS_KEY: CANT_ADD_ARCHIVED_COMPANY_MESSAGE,
            }
            raise serializers.ValidationError(errors)

        adviser = request.user
        default_legacy_list = _get_default_list_for_user(adviser)

        # get_or_create() is used to avoid an error if there is an existing
        # CompanyListItem for this adviser and company
        self.queryset.get_or_create(
            adviser=adviser,
            company=company,
            defaults={
                'list': default_legacy_list,
                'created_by': adviser,
                'modified_by': adviser,
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


def _get_default_list_for_user(adviser):
    company_list, _ = CompanyList.objects.get_or_create(
        adviser=adviser,
        is_legacy_default=True,
        defaults={
            'created_by': adviser,
            'name': DEFAULT_LEGACY_LIST_NAME,
            'modified_by': adviser,
        },
    )
    return company_list

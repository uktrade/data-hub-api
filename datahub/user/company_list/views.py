from django.db import transaction
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from datahub.company.models import Company, CompanyPermission
from datahub.core.query_utils import get_aggregate_subquery
from datahub.core.viewsets import CoreViewSet
from datahub.user.company_list.models import (
    CompanyList,
    CompanyListItem,
    CompanyListItemPermissionCode,
    PipelineItem,
    PipelineItemPermissionCode,
)
from datahub.user.company_list.queryset import (
    get_company_list_item_queryset,
    get_export_pipeline_item_queryset,
)
from datahub.user.company_list.serializers import (
    CompanyListItemSerializer,
    CompanyListSerializer,
    ExportPipelineItemSerializer,
)

CANT_ADD_ARCHIVED_COMPANY_MESSAGE = gettext_lazy(
    "An archived company can't be added to a company list.",
)


class CompanyListViewSet(CoreViewSet, DestroyModelMixin):
    """
    Views for managing the authenticated user's company lists.

    This covers:

    - creating a list
    - updating (i.e. renaming) a list
    - deleting a list
    - listing lists
    - retrieving details of a single list
    """

    queryset = CompanyList.objects.annotate(
        item_count=get_aggregate_subquery(CompanyList, Count('items')),
    )
    serializer_class = CompanyListSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ('items__company_id',)
    ordering = ('name', 'created_on', 'pk')

    def get_queryset(self):
        """Get a query set filtered to the authenticated user's lists."""
        return super().get_queryset().filter(adviser=self.request.user)

    def get_additional_data(self, create):
        """
        Set additional data for when serializer.save() is called.

        This makes sure that adviser is set to self.request.user when a list is created
        (in the same way created_by and modified_by are).
        """
        additional_data = super().get_additional_data(create)

        if not create:
            # A list is being updated rather than created, so leave the adviser field unchanged
            # (as there is no reason to change it)
            return additional_data

        return {
            **additional_data,
            'adviser': self.request.user,
        }


class CompanyListItemAPIPermissions(DjangoModelPermissions):
    """DRF permissions class for the company list item view."""

    perms_map = {
        'GET': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermissionCode.view_company_list_item}',
        ],
        'PUT': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermissionCode.add_company_list_item}',
        ],
        'DELETE': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{CompanyListItemPermissionCode.delete_company_list_item}',
        ],
    }


class ExportPipelineItemAPIPermissions(DjangoModelPermissions):
    """DRF permissions class for the export pipeline list item view."""

    perms_map = {
        'GET': [
            f'company.{CompanyPermission.view_company}',
            f'company_list.{PipelineItemPermissionCode.view_pipeline_item}',
        ],
    }


class CompanyListItemViewSet(CoreViewSet):
    """A view set for returning the contents of a company list."""

    permission_classes = (CompanyListItemAPIPermissions,)
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
        Raise an Http404 if user's company list specified in the URL path does not exist.
        """
        super().initial(request, *args, **kwargs)

        if not CompanyList.objects.filter(
            pk=self.kwargs['company_list_pk'],
            adviser=self.request.user,
        ).exists():
            raise Http404()

    def filter_queryset(self, queryset):
        """Filter the query set to the items relating to the authenticated users."""
        queryset = super().filter_queryset(queryset)
        return queryset.filter(list__pk=self.kwargs['company_list_pk'])


class ExportPipelineItemViewSet(CoreViewSet):
    """A view set for returning the contents of a export pipeline list."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        ExportPipelineItemAPIPermissions,
    )
    serializer_class = ExportPipelineItemSerializer
    queryset = get_export_pipeline_item_queryset()

    def get_queryset(self):
        """Get a query set filtered to the authenticated user's lists."""
        return super().get_queryset().filter(adviser=self.request.user)


class CompanyListItemAPIView(APIView):
    """
    A view for adding a company to a selected list of companies that belongs to a user.
    """

    permission_classes = (CompanyListItemAPIPermissions,)
    # Note: A query set is required for CompanyListItemPermissions
    queryset = CompanyListItem.objects.all()
    serializer_class = CompanyListItemSerializer

    @method_decorator(transaction.non_atomic_requests)
    def put(self, request, company_list_pk, company_pk, format=None):
        """Add company to a list."""
        company_list = self._get_company_list_or_404(request, company_list_pk)

        company = get_object_or_404(Company, pk=company_pk)
        if company.archived:
            errors = {
                api_settings.NON_FIELD_ERRORS_KEY: CANT_ADD_ARCHIVED_COMPANY_MESSAGE,
            }
            raise serializers.ValidationError(errors)

        adviser = request.user

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

    @method_decorator(transaction.non_atomic_requests)
    def delete(self, request, company_list_pk, company_pk=None, format=None):
        """
        Delete a CompanyListItem for the selected list of authenticated user and
        specified company if it exists.
        """
        company_list = get_object_or_404(CompanyList, pk=company_list_pk, adviser=request.user)
        company = get_object_or_404(Company, pk=company_pk)

        self.queryset.filter(list=company_list, company=company).delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def _get_company_list_or_404(self, request, company_list_pk):
        obj = get_object_or_404(
            CompanyList,
            adviser=request.user,
            pk=company_list_pk,
        )
        self.check_object_permissions(request, obj)
        return obj

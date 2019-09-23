from rest_framework.views import APIView

from config.settings.types import HawkScope
from datahub.company.models.contact import Contact
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.query_utils import get_full_name_expression
from datahub.dataset.contact.pagination import ContactsDatasetViewCursorPagination
from datahub.metadata.query_utils import get_sector_name_subquery


class ContactsDatasetView(HawkResponseSigningMixin, APIView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for
    Contacts Dataset to be consumed by Data-flow periodically. Data-flow uses response result
    to insert data into Dataworkspace through its defined API endpoints. The goal is presenting
    various reports to the users out of flattened table and let analyst to work on denormalized
    table to get more meaningful insight.
    """

    authentication_classes = (HawkAuthentication, )
    permission_classes = (HawkScopePermission, )
    required_hawk_scope = HawkScope.data_flow_api
    pagination_class = ContactsDatasetViewCursorPagination

    def get(self, request):
        """Endpoint which serves all records for Contacts Dataset"""
        dataset = self.get_dataset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        return paginator.get_paginated_response(page)

    def get_dataset(self):
        """Returns list of Contacts Dataset records"""
        return Contact.objects.annotate(
            name=get_full_name_expression(),
            company_sector=get_sector_name_subquery('company__sector'),
        ).values(
            'accepts_dit_email_marketing',
            'address_country__name',
            'address_postcode',
            'company__company_number',
            'company__name',
            'company__uk_region__name',
            'company_sector',
            'created_on',
            'email',
            'email_alternative',
            'job_title',
            'name',
            'notes',
            'telephone_alternative',
            'telephone_number',
        )

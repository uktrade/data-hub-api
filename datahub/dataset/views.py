from django.db.models import OuterRef, Subquery, Value
from django.db.models.functions import Concat
from rest_framework.views import APIView

from config.settings.types import HawkScope
from datahub.company.models.contact import Contact
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.model_helpers import get_m2m_model
from datahub.core.query_utils import (
    get_front_end_url_expression,
    get_full_name_expression,
    get_string_agg_subquery,
    get_top_related_expression_subquery,
)
from datahub.dataset.pagination import (
    ContactsDatasetViewCursorPagination,
    InteractionsDatasetViewCursorPagination,
    OMISDatasetViewCursorPagination,
)
from datahub.interaction.models import Interaction, InteractionDITParticipant
from datahub.interaction.queryset import get_base_interaction_queryset
from datahub.metadata.query_utils import get_sector_name_subquery, get_service_name_subquery
from datahub.omis.order.models import Order


class OMISDatasetView(HawkResponseSigningMixin, APIView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for OMIS Dataset
    to be consumed by Data-flow periodically. Data-flow uses response result to insert data into
    Dataworkspace through its defined API endpoints. The goal is presenting various reports to the
    users out of flattened table and let analyst to work on denormalized table to get
    more meaningful insight.
    """

    authentication_classes = (HawkAuthentication, )
    permission_classes = (HawkScopePermission, )
    required_hawk_scope = HawkScope.data_flow_api
    pagination_class = OMISDatasetViewCursorPagination

    def get(self, request):
        """Endpoint which serves all records for OMIS Dataset"""
        dataset = self.get_dataset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        return paginator.get_paginated_response(page)

    def get_dataset(self):
        """Returns list of OMIS Dataset records"""
        return Order.objects.annotate(
            services=get_string_agg_subquery(Order, 'service_types__name'),
        ).values(
            'cancelled_on',
            'cancellation_reason__name',
            'company__name',
            'company__address_1',
            'company__address_2',
            'company__address_town',
            'company__address_county',
            'company__address_country__name',
            'company__address_postcode',
            'company__registered_address_1',
            'company__registered_address_2',
            'company__registered_address_town',
            'company__registered_address_county',
            'company__registered_address_country__name',
            'company__registered_address_postcode',
            'completed_on',
            'contact__first_name',
            'contact__last_name',
            'contact__telephone_number',
            'contact__email',
            'created_by__dit_team__name',
            'created_on',
            'delivery_date',
            'invoice__subtotal_cost',
            'paid_on',
            'primary_market__name',
            'reference',
            'sector__segment',
            'services',
            'status',
            'subtotal_cost',
            'uk_region__name',
        )


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


class InteractionsDatasetView(HawkResponseSigningMixin, APIView):
    """
    A GET API view to return all interaction and service delivery data as required
    for syncing by Data-flow periodically.

    Data-flow uses the resulting response to insert data into Dataworkspace which can
    then be queried to create custom reports for users.
    """

    authentication_classes = (HawkAuthentication, )
    permission_classes = (HawkScopePermission, )
    required_hawk_scope = HawkScope.data_flow_api
    pagination_class = InteractionsDatasetViewCursorPagination

    def get(self, request):
        """Endpoint which serves all records for service deliveries and interactions dataset"""
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(self.get_dataset(), request, view=self)
        return paginator.get_paginated_response(page)

    def get_dataset(self):
        """Returns a list of all interaction and service delivery records"""
        contacts_m2m_model = get_m2m_model(Interaction, 'contacts')
        first_contact_queryset = contacts_m2m_model.objects.filter(
            interaction_id=OuterRef('pk'),
        ).order_by(
            'pk',
        )[:1]
        return get_base_interaction_queryset().annotate(
            sector=get_sector_name_subquery('company__sector'),
            contacts_name=get_full_name_expression(person_field_name='contacts'),
            interaction_link=get_front_end_url_expression('interaction', 'pk'),
            adviser_name=get_top_related_expression_subquery(
                InteractionDITParticipant.interaction.field,
                get_full_name_expression('adviser'),
                ('-id',),
            ),
            adviser_phone=get_top_related_expression_subquery(
                InteractionDITParticipant.interaction.field,
                'adviser__telephone_number',
                ('-id',),
            ),
            adviser_email=get_top_related_expression_subquery(
                InteractionDITParticipant.interaction.field,
                'adviser__email',
                ('-id',),
            ),
            adviser_team=get_top_related_expression_subquery(
                InteractionDITParticipant.interaction.field,
                'adviser__dit_team__name',
                ('-id',),
            ),
            service_delivery=get_service_name_subquery('service'),
            event_service=get_service_name_subquery('event__service'),
            contact_first_name=Subquery(first_contact_queryset.values('contact__first_name')),
            contact_last_name=Subquery(first_contact_queryset.values('contact__last_name')),
            contact_name=Concat('contact_first_name', Value(' '), 'contact_last_name'),
            contact_telephone_number=Subquery(
                first_contact_queryset.values('contact__telephone_number'),
            ),
            contact_email=Subquery(first_contact_queryset.values('contact__email')),
            contact_address_postcode=Subquery(
                first_contact_queryset.values('contact__address_postcode'),
            ),
            contact_address_1=Subquery(first_contact_queryset.values('contact__address_1')),
            contact_address_2=Subquery(first_contact_queryset.values('contact__address_2')),
            contact_address_town=Subquery(first_contact_queryset.values('contact__address_town')),
            contact_address_country=Subquery(
                first_contact_queryset.values('contact__address_country__name'),
            ),
        ).values(
            'date',
            'kind',
            'company__name',
            'company__company_number',
            'company__id',
            'investment_project__cdms_project_code',
            'company__address_postcode',
            'company__address_1',
            'company__address_2',
            'company__address_town',
            'company__address_country__name',
            'company__website',
            'company__employee_range__name',
            'company__turnover_range__name',
            'sector',
            'contact_name',
            'contact_telephone_number',
            'contact_email',
            'contact_address_postcode',
            'contact_address_1',
            'contact_address_2',
            'contact_address_town',
            'contact_address_country',
            'adviser_name',
            'adviser_phone',
            'adviser_email',
            'adviser_team',
            'company__uk_region__name',
            'service_delivery',
            'subject',
            'notes',
            'net_company_receipt',
            'grant_amount_offered',
            'service_delivery_status__name',
            'event__name',
            'event__event_type__name',
            'event__start_date',
            'event__address_town',
            'event__address_country__name',
            'event__uk_region__name',
            'event_service',
            'created_on',
            'communication_channel__name',
            'interaction_link',
        )

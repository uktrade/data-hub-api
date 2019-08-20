from django.db.models import F
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.settings.types import HawkScope
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.omis.order.models import Order


class OMISDatasetView(HawkResponseSigningMixin, APIView):
    """
    An APIView that provides 'get' action which queries and returns desired
    fields for OMIS Dataset to be consumed by dataworkspace
    """

    authentication_classes = (HawkAuthentication, )
    permission_classes = (HawkScopePermission, )
    required_hawk_scope = HawkScope.data_flow_api

    def get(self, request, format=None, company_pk=None):
        """Endpoint which serves all records for OMIS Dataset"""
        dataset = self.get_dataset()
        return Response(dataset, status=status.HTTP_200_OK)

    def get_dataset(self):
        """Returns constructed django queryset for OMIS Dataset"""
        queryset = Order.objects.prefetch_related('service_types').values(
            'delivery_date',
            order_id=F('id'),
            omis_order_reference=F('reference'),
            net_price=F('subtotal_cost'),
            subtotal=F('invoice__subtotal_cost'),
            company_name=F('company__name'),
            DIT_team=F('created_by__dit_team__name'),
            market=F('primary_market__name'),
            created_date=F('created_on'),
            cancelled_date=F('cancelled_on'),
            cancellation_reason_text=F('cancellation_reason__name'),
            UK_region=F('uk_region__name'),
            sector_name=F('sector__segment'),
            payment_received_date=F('paid_on'),
            completion_date=F('completed_on'),
            contact_first_name=F('contact__first_name'),
            contact_last_name=F('contact__last_name'),
            contact_phone_number=F('contact__telephone_number'),
            contact_email_address=F('contact__email'),
            company_trading_address_line_1=F('company__address_1'),
            company_trading_address_line_2=F('company__address_2'),
            company_trading_address_town=F('company__address_town'),
            company_trading_address_county=F('company__address_county'),
            company_trading_address_country=F('company__address_country__name'),
            company_trading_address_postcode=F('company__address_postcode'),
            company_registered_address_line_1=F('company__registered_address_1'),
            company_registered_address_line_2=F('company__registered_address_2'),
            company_registered_address_town=F('company__registered_address_town'),
            company_registered_address_county=F('company__registered_address_county'),
            company_registered_address_country=F('company__registered_address_country__name'),
            company_registered_address_postcode=F('company__registered_address_postcode'),
        )
        dataset = []
        for record in queryset.all():
            record['services'] = ', '.join(str(st.name) for st in Order.objects.get(
                id=record['order_id']).service_types.all())

            del record['order_id']
            dataset.append(record)

        return dataset

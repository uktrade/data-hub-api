import uuid

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.omis.order.test.factories import OrderFactory, OrderWithAcceptedQuoteFactory


class TestGetInvoice(APITestMixin):
    """Get invoice test case."""

    def test_get(self):
        """Test a successful call to get a invoice."""
        order = OrderWithAcceptedQuoteFactory()
        invoice = order.invoice

        url = reverse('api-v3:omis:invoice:detail', kwargs={'order_pk': order.pk})
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'created_on': format_date_or_datetime(invoice.created_on),
            'invoice_number': invoice.invoice_number,
            'invoice_company_name': invoice.invoice_company_name,
            'invoice_address_1': invoice.invoice_address_1,
            'invoice_address_2': invoice.invoice_address_2,
            'invoice_address_county': invoice.invoice_address_county,
            'invoice_address_town': invoice.invoice_address_town,
            'invoice_address_postcode': invoice.invoice_address_postcode,
            'invoice_address_country': {
                'id': str(invoice.invoice_address_country.pk),
                'name': invoice.invoice_address_country.name
            },
            'invoice_vat_number': invoice.invoice_vat_number,
            'payment_due_date': invoice.payment_due_date.isoformat(),

            'billing_contact_name': order.billing_contact_name,
            'billing_address_1': order.billing_address_1,
            'billing_address_2': order.billing_address_2,
            'billing_address_county': order.billing_address_county,
            'billing_address_postcode': order.billing_address_postcode,
            'billing_address_town': order.billing_address_town,
            'billing_address_country': {
                'id': str(order.billing_address_country.pk),
                'name': order.billing_address_country.name
            },
            'po_number': order.po_number,
        }

    def test_404_if_order_doesnt_exist(self):
        """Test that if the order doesn't exist, the endpoint returns 404."""
        url = reverse('api-v3:omis:invoice:detail', kwargs={'order_pk': uuid.uuid4()})
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_if_invoice_doesnt_exist(self):
        """Test that if the invoice doesn't exist, the endpoint returns 404."""
        order = OrderFactory()
        assert not order.invoice

        url = reverse('api-v3:omis:invoice:detail', kwargs={'order_pk': order.pk})
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

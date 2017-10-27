from unittest import mock
import pytest
from dateutil.parser import parse as dateutil_parse

from datahub.company.test.factories import AdviserFactory
from datahub.omis.order.test.factories import OrderPaidFactory

from ..models import Payment


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestPaymentManager:
    """Tests for the Payment Manager."""

    @mock.patch('datahub.omis.payment.managers.generate_datetime_based_reference')
    def test_create_from_order(
        self,
        mocked_generate_datetime_based_reference
    ):
        """Test that Payment.objects.create_from_order creates a payment."""
        mocked_generate_datetime_based_reference.return_value = '201702010004'

        order = OrderPaidFactory()
        by = AdviserFactory()
        attrs = {
            'transaction_reference': 'lorem ipsum',
            'amount': 1001,
            'received_on': dateutil_parse('2017-01-01').date()
        }
        payment = Payment.objects.create_from_order(
            order=order, by=by, attrs=attrs
        )

        payment.refresh_from_db()
        assert payment.reference == '201702010004'
        assert payment.created_by == by
        assert payment.order == order
        assert payment.transaction_reference == attrs['transaction_reference']
        assert payment.additional_reference == ''
        assert payment.amount == attrs['amount']
        assert payment.received_on == attrs['received_on']

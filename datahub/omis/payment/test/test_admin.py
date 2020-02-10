import pytest
from dateutil.parser import parse as dateutil_parse
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import AdminTestMixin
from datahub.omis.order.test.factories import OrderPaidFactory, OrderWithOpenQuoteFactory
from datahub.omis.payment.constants import PaymentMethod, RefundStatus
from datahub.omis.payment.models import Refund
from datahub.omis.payment.test.factories import (
    ApprovedRefundFactory,
    RejectedRefundFactory,
    RequestedRefundFactory,
)


class TestRefundAdmin(AdminTestMixin):
    """Tests for the Refund Admin."""

    def test_add(self):
        """
        Test adding a refund with status 'Approved'.
        This is the only status allowed when creating a record at the moment.
        """
        order = OrderPaidFactory()
        now_datetime = now()
        now_date_str = now_datetime.date().isoformat()
        now_time_str = now_datetime.time().isoformat()

        assert Refund.objects.count() == 0

        url = reverse('admin:omis-payment_refund_add')
        data = {
            'order': order.pk,
            'status': RefundStatus.APPROVED,
            'requested_on_0': now_date_str,
            'requested_on_1': now_time_str,
            'requested_by': AdviserFactory().pk,
            'requested_amount': order.total_cost,
            'refund_reason': 'lorem ipsum refund reason',
            'level1_approved_on_0': now_date_str,
            'level1_approved_on_1': now_time_str,
            'level1_approved_by': AdviserFactory().pk,
            'level1_approval_notes': 'lorem ipsum level 1',
            'level2_approved_on_0': now_date_str,
            'level2_approved_on_1': now_time_str,
            'level2_approved_by': AdviserFactory().pk,
            'level2_approval_notes': 'lorem ipsum level 2',
            'method': PaymentMethod.BACS,
            'net_amount': order.total_cost - 1,
            'vat_amount': 1,
            'additional_reference': 'additional reference',
            'rejection_reason': 'lorem ipsum rejection reason',
        }
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK

        assert Refund.objects.count() == 1
        refund = Refund.objects.first()

        assert refund.order.pk == data['order']
        assert refund.status == data['status']
        assert refund.requested_on == now_datetime
        assert refund.requested_by.pk == data['requested_by']
        assert refund.requested_amount == data['requested_amount']
        assert refund.refund_reason == data['refund_reason']
        assert refund.level1_approved_on == now_datetime
        assert refund.level1_approved_by.pk == data['level1_approved_by']
        assert refund.level1_approval_notes == data['level1_approval_notes']
        assert refund.level2_approved_on == now_datetime
        assert refund.level2_approved_by.pk == data['level2_approved_by']
        assert refund.level2_approval_notes == data['level2_approval_notes']
        assert refund.method == data['method']
        assert refund.net_amount == data['net_amount']
        assert refund.vat_amount == data['vat_amount']
        assert refund.additional_reference == data['additional_reference']
        assert refund.rejection_reason == data['rejection_reason']

        assert refund.total_amount == order.total_cost
        assert refund.created_by == self.user
        assert refund.modified_by == self.user
        assert not refund.payment

    @pytest.mark.parametrize(
        'refund_factory',
        (
            RequestedRefundFactory,
            ApprovedRefundFactory,
            RejectedRefundFactory,
        ),
    )
    def test_change(self, refund_factory):
        """Test changing a refund record, its status cannot change at this point."""
        refund = refund_factory()
        order = OrderPaidFactory()

        now_datetime = now()
        now_date_str = now_datetime.date().isoformat()
        now_time_str = now_datetime.time().isoformat()

        url = reverse('admin:omis-payment_refund_change', args=(refund.id,))
        data = {
            'order': order.pk,
            'status': refund.status,
            'requested_on_0': now_date_str,
            'requested_on_1': now_time_str,
            'requested_by': AdviserFactory().pk,
            'requested_amount': order.total_cost,
            'refund_reason': 'lorem ipsum refund reason',
            'level1_approved_on_0': now_date_str,
            'level1_approved_on_1': now_time_str,
            'level1_approved_by': AdviserFactory().pk,
            'level1_approval_notes': 'lorem ipsum level 1',
            'level2_approved_on_0': now_date_str,
            'level2_approved_on_1': now_time_str,
            'level2_approved_by': AdviserFactory().pk,
            'level2_approval_notes': 'lorem ipsum level 2',
            'method': PaymentMethod.BACS,
            'net_amount': order.total_cost - 1,
            'vat_amount': 1,
            'additional_reference': 'additional reference',
            'rejection_reason': 'lorem ipsum rejection reason',
        }
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK
        refund.refresh_from_db()

        assert refund.order.pk == data['order']
        assert refund.status == data['status']
        assert refund.requested_on == now_datetime
        assert refund.requested_by.pk == data['requested_by']
        assert refund.requested_amount == data['requested_amount']
        assert refund.refund_reason == data['refund_reason']
        assert refund.level1_approved_on == now_datetime
        assert refund.level1_approved_by.pk == data['level1_approved_by']
        assert refund.level1_approval_notes == data['level1_approval_notes']
        assert refund.level2_approved_on == now_datetime
        assert refund.level2_approved_by.pk == data['level2_approved_by']
        assert refund.level2_approval_notes == data['level2_approval_notes']
        assert refund.method == data['method']
        assert refund.net_amount == data['net_amount']
        assert refund.vat_amount == data['vat_amount']
        assert refund.additional_reference == data['additional_reference']
        assert refund.rejection_reason == data['rejection_reason']

        assert refund.total_amount == order.total_cost
        assert refund.created_by != self.user
        assert refund.modified_by == self.user
        assert not refund.payment

    @pytest.mark.parametrize(
        'data_delta,errors',
        (
            # invalid status
            (
                {'status': RefundStatus.REJECTED},
                {
                    'status': [
                        'Select a valid choice. rejected is not one of the available choices.',
                    ],
                },
            ),

            # invalid order status
            (
                {'order': lambda *_: OrderWithOpenQuoteFactory()},
                {'order': ['This order has not been paid for.']},
            ),

            # requested on < order.paid_on
            (
                {
                    'order': lambda *_: OrderPaidFactory(
                        paid_on=dateutil_parse('2018-01-01T13:00Z'),
                    ),
                    'requested_on_0': '2018-01-01',
                    'requested_on_1': '12:59',
                },
                {
                    'requested_on': [
                        'Please specify a value greater than or equal to Jan. 1, 2018, 1 p.m..',
                    ],
                },
            ),

            # level1 approved on < order.paid_on
            (
                {
                    'order': lambda *_: OrderPaidFactory(
                        paid_on=dateutil_parse('2018-01-01T13:00Z'),
                    ),
                    'level1_approved_on_0': '2018-01-01',
                    'level1_approved_on_1': '12:59',
                },
                {
                    'level1_approved_on': [
                        'Please specify a value greater than or equal to Jan. 1, 2018, 1 p.m..',
                    ],
                },
            ),

            # level2 approved on < order.paid_on
            (
                {
                    'order': lambda *_: OrderPaidFactory(
                        paid_on=dateutil_parse('2018-01-01T13:00Z'),
                    ),
                    'level2_approved_on_0': '2018-01-01',
                    'level2_approved_on_1': '12:59',
                },
                {
                    'level2_approved_on': [
                        'Please specify a value greater than or equal to Jan. 1, 2018, 1 p.m..',
                    ],
                },
            ),

            # same level1 and level2 approver
            (
                {
                    'level1_approved_by': lambda *_: AdviserFactory().pk,
                    'level2_approved_by': lambda _, d: d['level1_approved_by'],
                },
                {
                    'level1_approved_by': ['Approvers level1 and level2 have to be different.'],
                },
            ),

            # net_amount + vat_amount > order.total_cost
            (
                {
                    'net_amount': lambda o, _: o.total_cost,
                    'vat_amount': lambda *_: 1,
                },
                {
                    'net_amount': lambda o, _: [
                        f'Remaining amount that can be refunded: {o.total_cost}.',
                    ],
                },
            ),
        ),
    )
    def test_validation_error(self, data_delta, errors):
        """Test validation errors."""
        def resolve(value, order, data):
            if callable(value):
                return value(order, data)
            return value

        order = data_delta.pop('order', None) or OrderPaidFactory()
        order = resolve(order, None, None)

        now_datetime = now()
        now_date_str = now_datetime.date().isoformat()
        now_time_str = now_datetime.time().isoformat()

        url = reverse('admin:omis-payment_refund_add')
        data = {
            'order': order.pk,
            'status': RefundStatus.APPROVED,
            'requested_on_0': now_date_str,
            'requested_on_1': now_time_str,
            'requested_by': AdviserFactory().pk,
            'requested_amount': order.total_cost,
            'refund_reason': 'lorem ipsum refund reason',
            'level1_approved_on_0': now_date_str,
            'level1_approved_on_1': now_time_str,
            'level1_approved_by': AdviserFactory().pk,
            'level1_approval_notes': 'lorem ipsum level 1',
            'level2_approved_on_0': now_date_str,
            'level2_approved_on_1': now_time_str,
            'level2_approved_by': AdviserFactory().pk,
            'level2_approval_notes': 'lorem ipsum level 2',
            'method': PaymentMethod.BACS,
            'net_amount': order.total_cost - 1,
            'vat_amount': 1,
            'additional_reference': 'additional reference',
        }

        for data_key, data_value in data_delta.items():
            data[data_key] = resolve(data_value, order, data)
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK

        form = response.context['adminform'].form
        assert not form.is_valid()

        for error_key, error_value in errors.items():
            errors[error_key] = resolve(error_value, order, errors)
        assert form.errors == errors

    @pytest.mark.parametrize(
        'refund_factory,required_fields',
        (
            (
                RequestedRefundFactory,
                (
                    'order',
                    'status',
                    'requested_on',
                    'requested_amount',
                ),
            ),
            (
                ApprovedRefundFactory,
                (
                    'order',
                    'status',
                    'requested_on',
                    'requested_amount',
                    'level1_approved_on',
                    'level1_approved_by',
                    'level2_approved_on',
                    'level2_approved_by',
                    'method',
                    'net_amount',
                    'vat_amount',
                ),
            ),
            (
                RejectedRefundFactory,
                (
                    'order',
                    'status',
                    'requested_on',
                    'requested_amount',
                ),
            ),
        ),
    )
    def test_required_fields(self, refund_factory, required_fields):
        """Test required fields depending on the status of the refund."""
        refund = refund_factory()

        url = reverse('admin:omis-payment_refund_change', args=(refund.id,))
        data = {
            'order': '',
            'status': '',
            'requested_on_0': '',
            'requested_on_1': '',
            'requested_by': '',
            'requested_amount': '',
            'refund_reason': '',
            'level1_approved_on_0': '',
            'level1_approved_on_1': '',
            'level1_approved_by': '',
            'level1_approval_notes': '',
            'level2_approved_on_0': '',
            'level2_approved_on_1': '',
            'level2_approved_by': '',
            'level2_approval_notes': '',
            'method': '',
            'net_amount': '',
            'vat_amount': '',
            'additional_reference': '',
            'rejection_reason': '',
        }
        response = self.client.post(url, data, follow=True)

        form = response.context['adminform'].form
        assert not form.is_valid()

        assert form.errors == {
            required_field: ['This field is required.']
            for required_field in required_fields
        }

    @pytest.mark.parametrize(
        'refund_factory',
        (
            RequestedRefundFactory,
            ApprovedRefundFactory,
            RejectedRefundFactory,
        ),
    )
    def test_cannot_change_status(self, refund_factory):
        """Test that the status field cannot be changed at any point."""
        refund = refund_factory()

        now_datetime = now()
        date_str = now_datetime.date().isoformat()
        time_str = now_datetime.time().isoformat()

        url = reverse('admin:omis-payment_refund_change', args=(refund.id,))
        default_data = {
            'order': refund.order.pk,
            'requested_on_0': date_str,
            'requested_on_1': time_str,
            'requested_amount': refund.requested_amount,
            'refund_reason': refund.refund_reason,
            'level1_approved_on_0': date_str,
            'level1_approved_on_1': time_str,
            'level1_approved_by': AdviserFactory().pk,
            'level2_approved_on_0': date_str,
            'level2_approved_on_1': time_str,
            'level2_approved_by': AdviserFactory().pk,
            'method': refund.method or '',
            'net_amount': '' if refund.net_amount is None else refund.net_amount,
            'vat_amount': '' if refund.vat_amount is None else refund.vat_amount,
        }

        for changed_status, _ in RefundStatus.choices:
            if changed_status == refund.status:
                continue

            data = {
                **default_data,
                'status': changed_status,
            }
            response = self.client.post(url, data, follow=True)

            assert response.status_code == status.HTTP_200_OK
            form = response.context['adminform'].form
            assert not form.is_valid()
            assert form.errors == {
                'status': [
                    f'Select a valid choice. {changed_status} is not one of the available '
                    f'choices.',
                ],
            }

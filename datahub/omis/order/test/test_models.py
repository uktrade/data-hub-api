import secrets
from functools import partial
from unittest import mock

import factory
import pytest
from dateutil.parser import parse as dateutil_parse
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.exceptions import APIConflictException
from datahub.metadata.test.factories import TeamFactory
from datahub.omis.invoice.models import Invoice
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import CancellationReason
from datahub.omis.order.test.factories import (
    OrderAssigneeCompleteFactory,
    OrderAssigneeFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderWithAcceptedQuoteFactory,
    OrderWithOpenQuoteFactory,
)
from datahub.omis.payment.models import Payment
from datahub.omis.quote.models import Quote

pytestmark = pytest.mark.django_db


class OrderWithRandomPublicTokenFactory(OrderFactory):
    """OrderFactory with an already populated public_token field."""

    public_token = factory.LazyFunction(partial(secrets.token_urlsafe, 37))


class OrderWithRandomReferenceFactory(OrderFactory):
    """OrderFactory with an already populated reference field."""

    reference = factory.LazyFunction(get_random_string)


class TestGetLeadAssignee:
    """Tests for the get_lead_assignee() logic."""

    def test_without_assignees(self):
        """
        Test that get_lead_assignee() returns None if there are no assignees.
        """
        order = OrderFactory(assignees=[])
        assert not order.get_lead_assignee()

    def test_without_lead_assignee(self):
        """
        Test that get_lead_assignee() returns None if there are assignees
        but none of them is a lead.
        """
        order = OrderFactory(assignees=[])
        OrderAssigneeFactory(order=order, is_lead=False)
        assert not order.get_lead_assignee()

    def test_with_lead_assignee(self):
        """
        Test that get_lead_assignee() returns the lead assignee if present.
        """
        order = OrderFactory(assignees=[])
        lead_assignee = OrderAssigneeFactory(order=order, is_lead=True)
        OrderAssigneeFactory(order=order, is_lead=False)
        assert order.get_lead_assignee() == lead_assignee


class TestOrderGenerateReference:
    """Tests for the generate reference logic."""

    @freeze_time('2017-07-12 13:00:00.000000')
    @mock.patch('datahub.omis.order.models.get_random_string')
    def test_generates_reference_if_doesnt_exist(self, mock_get_random_string):
        """
        Test that if an Order is saved without reference, the system generates one automatically.
        """
        mock_get_random_string.side_effect = [
            'ABC', '123', 'CBA', '321',
        ]

        # create 1st
        order = OrderWithRandomPublicTokenFactory()
        assert order.reference == 'ABC123/17'

        # create 2nd
        order = OrderWithRandomPublicTokenFactory()
        assert order.reference == 'CBA321/17'

    @freeze_time('2017-07-12 13:00:00.000000')
    @mock.patch('datahub.omis.order.models.get_random_string')
    def test_doesnt_generate_reference_if_present(self, mock_get_random_string):
        """
        Test that when creating a new Order, if the system generates a reference that already
        exists, it skips it and generates the next one.
        """
        # create existing Order with ref == 'ABC123/17'
        OrderWithRandomPublicTokenFactory(reference='ABC123/17')

        mock_get_random_string.side_effect = [
            'ABC', '123', 'CBA', '321',
        ]

        # ABC123/17 already exists so create CBA321/17 instead
        order = OrderWithRandomPublicTokenFactory()
        assert order.reference == 'CBA321/17'

    @freeze_time('2017-07-12 13:00:00.000000')
    @mock.patch('datahub.omis.order.models.get_random_string')
    def test_cannot_generate_reference(self, mock_get_random_string):
        """
        Test that if there are more than 10 collisions, the generator algorithm raises a
        RuntimeError.
        """
        max_retries = 10
        OrderWithRandomPublicTokenFactory(reference='ABC123/17')

        mock_get_random_string.side_effect = ['ABC', '123'] * max_retries

        with pytest.raises(RuntimeError):
            for _ in range(max_retries):
                OrderWithRandomPublicTokenFactory()


class TestOrderGeneratePublicToken:
    """Tests for the generate public token logic."""

    @mock.patch('datahub.omis.order.models.secrets')
    def test_generates_public_token_if_doesnt_exist(self, mock_secrets):
        """
        Test that if an order is saved without public_token,
        the system generates one automatically.
        """
        mock_secrets.token_urlsafe.side_effect = ['9999', '8888']

        # create 1st
        order = OrderWithRandomReferenceFactory()
        assert order.public_token == '9999'

        # create 2nd
        order = OrderWithRandomReferenceFactory()
        assert order.public_token == '8888'

    @mock.patch('datahub.omis.order.models.secrets')
    def test_look_for_unused_public_token(self, mock_secrets):
        """
        Test that when creating a new order, if the system generates a public token
        that already exists, it skips it and generates the next one.
        """
        # create existing order with public_token == '9999'
        OrderWithRandomReferenceFactory(public_token='9999')

        mock_secrets.token_urlsafe.side_effect = ['9999', '8888']

        # 9999 already exists so create 8888 instead
        order = OrderWithRandomReferenceFactory()
        assert order.public_token == '8888'

    @mock.patch('datahub.omis.order.models.secrets')
    def test_cannot_generate_public_token(self, mock_secrets):
        """
        Test that if there are more than 10 collisions, the generator algorithm raises a
        RuntimeError.
        """
        max_retries = 10
        OrderWithRandomReferenceFactory(public_token='9999')

        mock_secrets.token_urlsafe.side_effect = ['9999'] * max_retries

        with pytest.raises(RuntimeError):
            for _ in range(max_retries):
                OrderWithRandomReferenceFactory()


class TestGenerateQuote:
    """Tests for the generate quote logic."""

    @mock.patch('datahub.omis.order.models.validators')
    def test_fails_with_incomplete_fields(self, validators):
        """Test raises ValidationError if the order is incomplete."""
        validators.OrderDetailsFilledInValidator.side_effect = ValidationError('error')

        order = OrderFactory()
        with pytest.raises(ValidationError):
            order.generate_quote(by=None)

    @mock.patch('datahub.omis.order.models.validators')
    def test_fails_if_theres_already_an_active_quote(self, validators):
        """Test raises APIConflictException if there's already an active quote."""
        validators.NoOtherActiveQuoteExistsValidator.side_effect = APIConflictException('error')

        order = OrderFactory()
        with pytest.raises(APIConflictException):
            order.generate_quote(by=None)

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.quote_accepted,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_fails_if_order_not_in_draft(self, disallowed_status):
        """Test that if the order is not in `draft`, a quote cannot be generated."""
        order = OrderFactory(status=disallowed_status)
        with pytest.raises(APIConflictException):
            order.generate_quote(by=None)

    def test_atomicity(self):
        """Test that if there's a problem with saving the order, the quote is not saved either."""
        order = OrderFactory()
        with mock.patch.object(order, 'save') as mocked_save:
            mocked_save.side_effect = Exception()

            with pytest.raises(Exception):
                order.generate_quote(by=None)
            assert not Quote.objects.count()

    def test_success(self):
        """Test that a quote can be generated."""
        company = CompanyFactory(
            registered_address_1='Reg address 1',
            registered_address_2='Reg address 2',
            registered_address_town='Reg address town',
            registered_address_county='Reg address county',
            registered_address_postcode='Reg address postcode',
            registered_address_country_id=constants.Country.japan.value.id,
        )
        order = OrderFactory(
            company=company,
            billing_company_name='',
            billing_contact_name='',
            billing_email='',
            billing_phone='',
            billing_address_1='',
            billing_address_2='',
            billing_address_town='',
            billing_address_county='',
            billing_address_postcode='',
            billing_address_country_id=None,
        )
        adviser = AdviserFactory()
        order.generate_quote(by=adviser)

        # quote created and populated
        assert order.quote.pk
        assert order.quote.reference
        assert order.quote.content
        assert order.quote.created_by == adviser

        # status changed
        assert order.status == OrderStatus.quote_awaiting_acceptance

        assert not order.billing_contact_name
        assert not order.billing_email
        assert not order.billing_phone

        # billing fields populated
        assert order.billing_company_name == company.name
        assert order.billing_address_1 == company.registered_address_1
        assert order.billing_address_2 == company.registered_address_2
        assert order.billing_address_county == company.registered_address_county
        assert order.billing_address_town == company.registered_address_town
        assert order.billing_address_postcode == company.registered_address_postcode
        assert order.billing_address_country == company.registered_address_country

    def test_without_committing(self):
        """Test that a quote can be generated without saving its changes."""
        order = OrderFactory()
        order.generate_quote(by=AdviserFactory(), commit=False)

        assert order.quote.reference
        assert order.quote.content
        assert order.status == OrderStatus.quote_awaiting_acceptance

        order.refresh_from_db()
        assert not order.quote
        assert not Quote.objects.count()
        assert order.status == OrderStatus.draft


class TestReopen:
    """Tests for when an order is reopened."""

    @pytest.mark.parametrize(
        'allowed_status',
        (
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.quote_accepted,
        ),
    )
    def test_ok_if_order_in_allowed_status(self, allowed_status):
        """
        Test that an order can be reopened if it's in one of the allowed statuses.
        """
        order = OrderFactory(status=allowed_status)

        order.reopen(by=AdviserFactory())

        assert order.status == OrderStatus.draft

    def test_with_active_quote(self):
        """
        Test that if an order with an active quote is reopened, the quote is cancelled.
        """
        order = OrderWithOpenQuoteFactory()
        assert not order.quote.is_cancelled()

        adviser = AdviserFactory()

        with freeze_time('2017-07-12 13:00'):
            order.reopen(by=adviser)

            assert order.quote.is_cancelled()
            assert order.quote.cancelled_by == adviser
            assert order.quote.cancelled_on == now()
            assert order.status == OrderStatus.draft

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.draft,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_fails_if_order_not_in_allowed_status(self, disallowed_status):
        """Test that if the order is in a disallowed status, it cannot be reopened."""
        order = OrderFactory(status=disallowed_status)
        with pytest.raises(APIConflictException):
            order.reopen(by=None)

        assert order.status == disallowed_status


class TestUpdateInvoiceDetails:
    """Tests for the update_invoice_details method."""

    def test_ok_if_order_in_quote_accepted(self):
        """
        Test that update_invoice_details creates a new invoice and links it to the order.
        """
        order = OrderWithAcceptedQuoteFactory()
        old_invoice = order.invoice

        order.update_invoice_details()

        order.refresh_from_db()
        assert order.invoice != old_invoice

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.draft,
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_fails_if_order_not_in_allowed_status(self, disallowed_status):
        """
        Test that if the order is in a disallowed status, the invoice details cannot be updated.
        """
        order = OrderFactory(status=disallowed_status)
        with pytest.raises(APIConflictException):
            order.update_invoice_details()

        assert order.status == disallowed_status


class TestAcceptQuote:
    """Tests for when a quote is accepted."""

    @pytest.mark.parametrize(
        'allowed_status',
        (OrderStatus.quote_awaiting_acceptance,),
    )
    def test_ok_if_order_in_allowed_status(self, allowed_status):
        """
        Test that the quote of an order can be accepted if the order is
        in one of the allowed statuses.
        """
        order = OrderWithOpenQuoteFactory(status=allowed_status)
        contact = ContactFactory()

        order.accept_quote(by=contact)

        order.refresh_from_db()
        assert order.status == OrderStatus.quote_accepted
        assert order.quote.accepted_on
        assert order.quote.accepted_by == contact
        assert order.invoice
        assert order.invoice.billing_company_name == order.billing_company_name
        assert order.invoice.billing_address_1 == order.billing_address_1
        assert order.invoice.billing_address_2 == order.billing_address_2
        assert order.invoice.billing_address_town == order.billing_address_town
        assert order.invoice.billing_address_county == order.billing_address_county
        assert order.invoice.billing_address_postcode == order.billing_address_postcode
        assert order.invoice.billing_address_country == order.billing_address_country
        assert order.invoice.po_number == order.po_number
        assert order.invoice.contact_email == order.get_current_contact_email()

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.quote_accepted,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_fails_if_order_not_in_allowed_status(self, disallowed_status):
        """Test that if the order is in a disallowed status, the quote cannot be accepted."""
        order = OrderFactory(status=disallowed_status)
        with pytest.raises(APIConflictException):
            order.accept_quote(by=None)

        assert order.status == disallowed_status

    def test_atomicity(self):
        """Test that if there's a problem with saving the order, the quote is not saved either."""
        order = OrderWithOpenQuoteFactory()
        with mock.patch.object(order, 'save') as mocked_save:
            mocked_save.side_effect = Exception()

            with pytest.raises(Exception):
                order.accept_quote(by=None)

            quote = order.quote
            order.refresh_from_db()
            quote.refresh_from_db()
            assert not quote.is_accepted()
            assert not order.invoice
            assert not Invoice.objects.count()


class TestMarkOrderAsPaid:
    """Tests for when an order is marked as paid."""

    @pytest.mark.parametrize(
        'allowed_status',
        (OrderStatus.quote_accepted,),
    )
    def test_ok_if_order_in_allowed_status(self, allowed_status):
        """
        Test that the order can be marked as paid if the order is in one of the allowed statuses.
        """
        order = OrderWithAcceptedQuoteFactory(status=allowed_status)
        adviser = AdviserFactory()

        order.mark_as_paid(
            by=adviser,
            payments_data=[
                {
                    'amount': 1,
                    'received_on': dateutil_parse('2017-01-01').date(),
                },
                {
                    'amount': order.total_cost - 1,
                    'received_on': dateutil_parse('2017-01-02').date(),
                },
            ],
        )

        order.refresh_from_db()
        assert order.status == OrderStatus.paid
        assert order.paid_on == dateutil_parse('2017-01-02T00:00:00Z')
        assert list(
            order.payments.order_by('received_on').values_list('amount', 'received_on'),
        ) == [
            (1, dateutil_parse('2017-01-01').date()),
            (order.total_cost - 1, dateutil_parse('2017-01-02').date()),
        ]

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.draft,
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_fails_if_order_not_in_allowed_status(self, disallowed_status):
        """
        Test that if the order is in a disallowed status, the order cannot be marked as paid.
        """
        order = OrderFactory(status=disallowed_status)
        with pytest.raises(APIConflictException):
            order.mark_as_paid(by=None, payments_data=[])

        assert order.status == disallowed_status

    def test_atomicity(self):
        """
        Test that if there's a problem with saving the order, the payments are not saved either.
        """
        order = OrderWithAcceptedQuoteFactory()
        with mock.patch.object(order, 'save') as mocked_save:
            mocked_save.side_effect = Exception()

            with pytest.raises(Exception):
                order.mark_as_paid(
                    by=None,
                    payments_data=[{
                        'amount': order.total_cost,
                        'received_on': dateutil_parse('2017-01-02').date(),
                    }],
                )

            order.refresh_from_db()
            assert order.status == OrderStatus.quote_accepted
            assert not order.paid_on
            assert not Payment.objects.count()

    def test_validation_error_if_amounts_less_then_total_cost(self):
        """
        Test that if the sum of the amounts is < order.total_cose, the call fails.
        """
        order = OrderWithAcceptedQuoteFactory()
        with pytest.raises(ValidationError):
            order.mark_as_paid(
                by=None,
                payments_data=[
                    {
                        'amount': order.total_cost - 1,
                        'received_on': dateutil_parse('2017-01-02').date(),
                    },
                ],
            )


class TestCompleteOrder:
    """Tests for when an order is marked as complete."""

    @pytest.mark.parametrize(
        'allowed_status',
        (OrderStatus.paid,),
    )
    def test_ok_if_order_in_allowed_status(self, allowed_status):
        """
        Test that the order can be marked as complete if it's in one of the allowed statuses.
        """
        order = OrderPaidFactory(status=allowed_status, assignees=[])
        OrderAssigneeCompleteFactory(order=order)
        adviser = AdviserFactory()

        with freeze_time('2018-07-12 13:00'):
            order.complete(by=adviser)

        order.refresh_from_db()
        assert order.status == OrderStatus.complete
        assert order.completed_on == dateutil_parse('2018-07-12T13:00Z')
        assert order.completed_by == adviser

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.draft,
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.quote_accepted,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_fails_if_order_not_in_allowed_status(self, disallowed_status):
        """
        Test that if the order is in a disallowed status, the order cannot be marked as complete.
        """
        order = OrderFactory(status=disallowed_status)
        with pytest.raises(APIConflictException):
            order.complete(by=None)

        assert order.status == disallowed_status

    def test_atomicity(self):
        """
        Test that if there's a problem with saving the order, nothing gets saved.
        """
        order = OrderPaidFactory(assignees=[])
        OrderAssigneeCompleteFactory(order=order)
        with mock.patch.object(order, 'save') as mocked_save:
            mocked_save.side_effect = Exception()

            with pytest.raises(Exception):
                order.complete(by=None)

            order.refresh_from_db()
            assert order.status == OrderStatus.paid
            assert not order.completed_on
            assert not order.completed_by

    def test_validation_error_if_not_all_actual_time_set(self):
        """
        Test that if not all assignee actual time fields have been set,
        a validation error is raised and the call fails.
        """
        order = OrderPaidFactory(assignees=[])
        OrderAssigneeCompleteFactory(order=order)
        OrderAssigneeFactory(order=order)

        with pytest.raises(ValidationError):
            order.complete(by=None)


class TestCancelOrder:
    """Tests for when an order is cancelled."""

    @pytest.mark.parametrize(
        'allowed_status,force',
        (
            # force=False
            (OrderStatus.draft, False),
            (OrderStatus.quote_awaiting_acceptance, False),

            # force=True
            (OrderStatus.draft, True),
            (OrderStatus.quote_awaiting_acceptance, True),
            (OrderStatus.quote_accepted, True),
            (OrderStatus.paid, True),
        ),
    )
    def test_ok_if_order_in_allowed_status(self, allowed_status, force):
        """
        Test that the order can be cancelled if it's in one of the allowed statuses.
        """
        reason = CancellationReason.objects.order_by('?').first()
        order = OrderFactory(status=allowed_status)
        adviser = AdviserFactory()

        with freeze_time('2018-07-12 13:00'):
            order.cancel(by=adviser, reason=reason, force=force)

        order.refresh_from_db()
        assert order.status == OrderStatus.cancelled
        assert order.cancelled_on == dateutil_parse('2018-07-12T13:00Z')
        assert order.cancellation_reason == reason
        assert order.cancelled_by == adviser

    @pytest.mark.parametrize(
        'disallowed_status,force',
        (
            # force=False
            (OrderStatus.quote_accepted, False),
            (OrderStatus.paid, False),
            (OrderStatus.complete, False),
            (OrderStatus.cancelled, False),

            # force=True
            (OrderStatus.complete, True),
            (OrderStatus.cancelled, True),
        ),
    )
    def test_fails_if_order_not_in_allowed_status(self, disallowed_status, force):
        """
        Test that if the order is in a disallowed status, the order cannot be cancelled.
        """
        reason = CancellationReason.objects.order_by('?').first()
        order = OrderFactory(status=disallowed_status)

        with pytest.raises(APIConflictException):
            order.cancel(by=None, reason=reason, force=force)

        assert order.status == disallowed_status

    def test_atomicity(self):
        """
        Test that if there's a problem with saving the order, nothing gets saved.
        """
        reason = CancellationReason.objects.order_by('?').first()
        order = OrderFactory(status=OrderStatus.draft)

        with mock.patch.object(order, 'save') as mocked_save:
            mocked_save.side_effect = Exception()

            with pytest.raises(Exception):
                order.cancel(by=None, reason=reason)

            order.refresh_from_db()
            assert order.status == OrderStatus.draft
            assert not order.cancellation_reason
            assert not order.cancelled_on
            assert not order.cancelled_by


class TestOrderAssignee:
    """Tests for the OrderAssignee model."""

    def test_set_team_country_on_create(self):
        """
        Tests that when creating a new OrderAssignee, the `team` and `country`
        properties get populated automatically.
        """
        # adviser belonging to a team with a country
        team = TeamFactory(country_id=constants.Country.france.value.id)
        adviser = AdviserFactory(dit_team=team)
        assignee = OrderAssigneeFactory(adviser=adviser)

        assert assignee.team == team
        assert str(assignee.country_id) == constants.Country.france.value.id

        # adviser belonging to a team without country
        team = TeamFactory(country=None)
        adviser = AdviserFactory(dit_team=team)
        assignee = OrderAssigneeFactory(adviser=adviser)

        assert assignee.team == team
        assert not assignee.country

        # adviser not belonging to any team
        adviser = AdviserFactory(dit_team=None)
        assignee = OrderAssigneeFactory(adviser=adviser)

        assert not assignee.team
        assert not assignee.country

    def test_team_country_dont_change_after_creation(self):
        """
        Tests that after creating an OrderAssignee, the `team` and `country`
        properties don't change with further updates.
        """
        team_france = TeamFactory(country_id=constants.Country.france.value.id)
        adviser = AdviserFactory(dit_team=team_france)
        assignee = OrderAssigneeFactory(adviser=adviser)

        # the adviser moves to another team
        adviser.dit_team = TeamFactory(country_id=constants.Country.italy.value.id)
        adviser.save()

        assignee.estimated_time = 1000
        assignee.save()
        assignee.refresh_from_db()

        # the assignee is still linking to the original team and country
        assert assignee.team == team_france
        assert str(assignee.country_id) == constants.Country.france.value.id

    def test_cannot_change_adviser_after_creation(self):
        """After creating an OrderAssignee, the related adviser cannot be changed."""
        adviser = AdviserFactory()
        assignee = OrderAssigneeFactory(adviser=adviser)

        with pytest.raises(ValueError):
            assignee.adviser = AdviserFactory()
            assignee.save()


def test_order_get_absolute_url():
    """Test that Order.get_absolute_url() returns the correct URL."""
    order = OrderFactory.build()
    assert order.get_absolute_url() == (
        f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["order"]}/{order.pk}'
    )

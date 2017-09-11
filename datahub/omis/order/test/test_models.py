from unittest import mock

import pytest
from freezegun import freeze_time

from rest_framework.exceptions import ValidationError

from datahub.company.test.factories import AdviserFactory
from datahub.core import constants
from datahub.metadata.test.factories import TeamFactory
from datahub.omis.core.exceptions import Conflict
from datahub.omis.quote.models import Quote

from .factories import (
    OrderAssigneeFactory,
    OrderFactory,
    OrderWithCancelledQuoteFactory,
    OrderWithOpenQuoteFactory,
)

from ..constants import OrderStatus


pytestmark = pytest.mark.django_db


class TestOrderGenerateReference:
    """
    Tests the generate reference logic for the Order model.
    """

    @freeze_time('2017-07-12 13:00:00.000000+00:00')
    @mock.patch('datahub.omis.order.models.get_random_string')
    def test_generates_reference_if_doesnt_exist(self, mock_get_random_string):
        """
        Test that if an Order is saved without reference, the system generates one automatically.
        """
        mock_get_random_string.side_effect = [
            'ABC', '123', 'CBA', '321'
        ]

        # create 1st
        order = OrderFactory()
        assert order.reference == 'ABC123/17'

        # create 2nd
        order = OrderFactory()
        assert order.reference == 'CBA321/17'

    @freeze_time('2017-07-12 13:00:00.000000+00:00')
    @mock.patch('datahub.omis.order.models.get_random_string')
    def test_doesnt_generate_reference_if_present(self, mock_get_random_string):
        """
        Test that when creating a new Order, if the system generates a reference that already
        exists, it skips it and generates the next one.
        """
        # create existing Order with ref == 'ABC123/17'
        OrderFactory(reference='ABC123/17')

        mock_get_random_string.side_effect = [
            'ABC', '123', 'CBA', '321'
        ]

        # ABC123/17 already exists so create CBA321/17 instead
        order = OrderFactory()
        assert order.reference == 'CBA321/17'

    @freeze_time('2017-07-12 13:00:00.000000+00:00')
    @mock.patch('datahub.omis.order.models.get_random_string')
    def test_cannot_generate_reference(self, mock_get_random_string):
        """
        Test that if there are more than 10 collisions, the generator algorithm raises a
        RuntimeError.
        """
        max_retries = 10
        OrderFactory(reference='ABC123/17')

        mock_get_random_string.side_effect = ['ABC', '123'] * max_retries

        with pytest.raises(RuntimeError):
            for index in range(max_retries):
                OrderFactory()


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
        """Test raises Conflict if there's already an active quote."""
        validators.NoOtherActiveQuoteExistsValidator.side_effect = Conflict('error')

        order = OrderFactory()
        with pytest.raises(Conflict):
            order.generate_quote(by=None)

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.quote_accepted,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        )
    )
    def test_fails_if_order_not_in_draft(self, disallowed_status):
        """Test that if the order is not in `draft`, a quote cannot be generated."""
        order = OrderFactory(status=disallowed_status)
        with pytest.raises(Conflict):
            order.generate_quote(by=None)

    def test_atomicity(self):
        """Test that if there's a problem with saving the order, the quote is not saved either."""
        order = OrderFactory()
        order.save = mock.Mock()
        order.save.side_effect = Exception()

        with pytest.raises(Exception):
            order.generate_quote(by=None)
        assert not Quote.objects.count()

    def test_success(self):
        """Test that a quote can be generated."""
        order = OrderFactory()
        adviser = AdviserFactory()
        order.generate_quote(by=adviser)

        assert order.quote.pk
        assert order.quote.reference
        assert order.quote.content
        assert order.quote.created_by == adviser
        assert order.status == OrderStatus.quote_awaiting_acceptance

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

    @pytest.mark.parametrize('allowed_status', (
        OrderStatus.draft,
        OrderStatus.quote_awaiting_acceptance,
        OrderStatus.quote_accepted,
    ))
    def test_ok_if_order_in_allowed_status(self, allowed_status):
        """
        Test that an order can be reopened if it's in one of the allowed statuses.
        """
        order = OrderFactory(status=allowed_status)

        try:
            order.reopen(by=AdviserFactory())
        except Exception:
            pytest.fail('Should not raise a validator error.')

        assert order.status == OrderStatus.draft

    def test_without_quote(self):
        """
        Test that if an order without quote is reopened, nothing happens as
        the order is already open.
        """
        order = OrderFactory()
        assert not order.quote

        order.reopen(by=AdviserFactory())
        assert not order.quote
        assert order.status == OrderStatus.draft

    def test_with_active_quote(self):
        """
        Test that if an order with an active quote is reopened, the quote is cancelled.
        """
        order = OrderWithOpenQuoteFactory()
        assert not order.quote.is_cancelled()

        adviser = AdviserFactory()

        with freeze_time('2017-07-12 13:00') as mocked_now:
            order.reopen(by=adviser)

            assert order.quote.is_cancelled()
            assert order.quote.cancelled_by == adviser
            assert order.quote.cancelled_on == mocked_now()
            assert order.status == OrderStatus.draft

    def test_with_already_cancelled_quote(self):
        """
        Test that if an order with an already cancelled quote is reopened, nothing happens.
        """
        order = OrderWithCancelledQuoteFactory()
        assert order.quote.is_cancelled()
        orig_cancelled_on = order.quote.cancelled_on
        orig_cancelled_by = order.quote.cancelled_by

        adviser = AdviserFactory()

        with freeze_time('2017-07-12 13:00') as mocked_now:
            order.reopen(by=adviser)

            assert order.quote.is_cancelled()
            assert order.quote.cancelled_by != adviser
            assert order.quote.cancelled_on != mocked_now()

            assert order.quote.cancelled_by == orig_cancelled_by
            assert order.quote.cancelled_on == orig_cancelled_on

            assert order.status == OrderStatus.draft

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        )
    )
    def test_fails_if_order_not_in_allowed_status(self, disallowed_status):
        """Test that if the order is in a disallowed status, it cannot be reopened."""
        order = OrderFactory(status=disallowed_status)
        with pytest.raises(Conflict):
            order.reopen(by=None)

        assert order.status == disallowed_status


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

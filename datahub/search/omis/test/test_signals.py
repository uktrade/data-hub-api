import pytest

from datahub.omis.order.test.factories import (
    OrderAssigneeFactory, OrderFactory,
    OrderSubscriberFactory, OrderWithOpenQuoteFactory
)
from .. import OrderSearchApp

pytestmark = pytest.mark.django_db


def test_creating_order_syncs_to_es(setup_es):
    """Test that when I create an order, it gets synced to ES."""
    order = OrderFactory()
    setup_es.indices.refresh()

    assert setup_es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk
    )


def test_updating_order_updates_es(setup_es):
    """Test that when I update an order, the updated version gets synced to ES."""
    order = OrderFactory()
    new_description = 'lorem'
    order.description = new_description
    order.save()
    setup_es.indices.refresh()

    result = setup_es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk
    )
    assert result['_source']['description'] == new_description


def test_accepting_quote_updates_es(setup_es):
    """
    Test that when a quote is accepted and the invoice created, the payment_due_date field
    in ES gets updated.
    """
    order = OrderWithOpenQuoteFactory()
    setup_es.indices.refresh()

    result = setup_es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk
    )
    assert not result['_source']['payment_due_date']

    order.accept_quote(by=None)
    setup_es.indices.refresh()

    result = setup_es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk
    )
    assert result['_source']['payment_due_date'] == order.invoice.payment_due_date.isoformat()


def test_adding_subscribers_syncs_order_to_es(setup_es):
    """
    Test that when a subscriber is added to an order,
    the linked order gets synced to ES.
    """
    order = OrderFactory()
    subscribers = OrderSubscriberFactory.create_batch(2, order=order)
    setup_es.indices.refresh()

    result = setup_es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk
    )

    indexed = {str(subscriber['id']) for subscriber in result['_source']['subscribers']}
    expected = {str(subscriber.adviser.pk) for subscriber in subscribers}
    assert indexed == expected
    assert len(indexed) == 2


def test_removing_subscribers_syncs_order_to_es(setup_es):
    """
    Test that when a subscriber is removed from an order,
    the linked order gets synced to ES.
    """
    order = OrderFactory()
    subscribers = OrderSubscriberFactory.create_batch(2, order=order)
    subscribers.pop().delete()
    setup_es.indices.refresh()

    result = setup_es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk
    )

    indexed = {str(subscriber['id']) for subscriber in result['_source']['subscribers']}
    expected = {str(subscriber.adviser.pk) for subscriber in subscribers}
    assert indexed == expected
    assert len(indexed) == 1


def test_adding_assignees_syncs_order_to_es(setup_es):
    """
    Test that when an assignee is added to an order,
    the linked order gets synced to ES.
    """
    order = OrderFactory(assignees=[])
    assignees = OrderAssigneeFactory.create_batch(2, order=order)
    setup_es.indices.refresh()

    result = setup_es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk
    )

    indexed = {str(assignee['id']) for assignee in result['_source']['assignees']}
    expected = {str(assignee.adviser.pk) for assignee in assignees}
    assert indexed == expected
    assert len(indexed) == 2


def test_removing_assignees_syncs_order_to_es(setup_es):
    """
    Test that when an assignee is removed from an order,
    the linked order gets synced to ES.
    """
    order = OrderFactory(assignees=[])
    assignees = OrderAssigneeFactory.create_batch(2, order=order)
    assignees.pop().delete()
    setup_es.indices.refresh()

    result = setup_es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk
    )

    indexed = {str(assignee['id']) for assignee in result['_source']['assignees']}
    expected = {str(assignee.adviser.pk) for assignee in assignees}
    assert indexed == expected
    assert len(indexed) == 1

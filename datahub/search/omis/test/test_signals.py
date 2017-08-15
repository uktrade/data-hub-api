import pytest

from django.conf import settings

from datahub.omis.order.test.factories import OrderFactory

from .. import OrderSearchApp

pytestmark = pytest.mark.django_db


def test_creating_order_syncs_to_es(setup_es):
    """Test that when I create an order, it gets synced to ES."""
    order = OrderFactory()
    setup_es.indices.refresh()

    assert setup_es.get(
        index=settings.ES_INDEX,
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
        index=settings.ES_INDEX,
        doc_type=OrderSearchApp.name,
        id=order.pk
    )
    assert result['_source']['description'] == new_description

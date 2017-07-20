from unittest import mock

import pytest
from freezegun import freeze_time

from datahub.omis.order.test.factories import OrderFactory

pytestmark = pytest.mark.django_db


class TestOrder:
    """
    Tests for the Order model.
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

from unittest import mock

import pytest
from dateutil.parser import parse as dateutil_parse
from rest_framework.exceptions import ValidationError

from datahub.omis.payment.validators import ReconcilablePaymentsSubValidator


class TestReconcilablePaymentsSubValidator:
    """Tests for the ReconcilablePaymentsSubValidator."""

    def test_ok_with_amounts_equal_total_cost(self):
        """
        Test that the validation succeeds when the sum of the amounts = order.total_cost.
        """
        validator = ReconcilablePaymentsSubValidator()
        order = mock.MagicMock(total_cost=1000)

        data = [
            {'amount': 600, 'received_on': dateutil_parse('2017-01-01').date()},
            {'amount': 400, 'received_on': dateutil_parse('2017-01-01').date()},
        ]

        try:
            validator(data, order)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_ok_with_amounts_greater_than_total_cost(self):
        """
        Test that the validation succeeds when the sum of the amounts > order.total_cost.
        """
        validator = ReconcilablePaymentsSubValidator()
        order = mock.MagicMock(total_cost=1000)
        data = [
            {'amount': 1000, 'received_on': dateutil_parse('2017-01-01').date()},
            {'amount': 1, 'received_on': dateutil_parse('2017-01-01').date()},
        ]

        try:
            validator(data, order)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_fails_with_amounts_less_than_total_cost(self):
        """
        Test that the validation fails when the sum of the amounts < order.total_cost.
        """
        validator = ReconcilablePaymentsSubValidator()
        order = mock.MagicMock(total_cost=1000)
        data = [
            {'amount': 998, 'received_on': dateutil_parse('2017-01-01').date()},
            {'amount': 1, 'received_on': dateutil_parse('2017-01-01').date()},
        ]

        with pytest.raises(ValidationError) as exc:
            validator(data, order)

        assert exc.value.detail == {
            'non_field_errors': (
                'The sum of the amounts has to be '
                'equal or greater than the order total.'
            ),
        }

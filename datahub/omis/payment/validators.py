from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings


class ReconcilablePaymentsSubValidator:
    """
    Validator which checks that the specified payments data can be
    reconciled, that is, their sum is equal or greater than the order total.

    This validator is designed for direct use rather than with a DRF serializer.
    """

    message = 'The sum of the amounts has to be equal or greater than the order total.'

    def __call__(self, data, order):
        """Validate that payments data can be reconciled."""
        if sum(item_data['amount'] for item_data in data) < order.total_cost:
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: self.message,
            })

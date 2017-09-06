from django.db import models

from .utils import generate_quote_content, generate_quote_reference


class QuoteManager(models.Manager):
    """Custom Quote Manager."""

    def create_from_order(self, order, by, commit=True):
        """
        :param order: Order instance for this quote
        :param by: who made the action
        :param commit: True if the changes have to be committed

        :returns: Quote object generated from the order
        """
        quote = self.model(
            created_by=by,
            reference=generate_quote_reference(order),
            content=generate_quote_content(order),
        )

        if commit:
            quote.save()

        return quote

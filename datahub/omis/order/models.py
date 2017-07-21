import uuid

from django.db import models
from django.utils.crypto import get_random_string
from django.utils.timezone import now

from datahub.company.models import Company, Contact
from datahub.core.models import BaseModel

from datahub.metadata.models import Country


class Order(BaseModel):
    """
    Details regarding an OMIS Order.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reference = models.CharField(max_length=100)

    company = models.ForeignKey(
        Company,
        related_name="%(class)ss",  # noqa: Q000
        on_delete=models.PROTECT,
    )
    contact = models.ForeignKey(
        Contact,
        related_name="%(class)ss",  # noqa: Q000
        on_delete=models.PROTECT
    )

    primary_market = models.ForeignKey(
        Country,
        related_name="%(class)ss",  # noqa: Q000
        null=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        """Human-readable representation"""
        return self.reference

    def _calculate_reference(self):
        """
        Returns a random unused reference of form:
            <(3) letters><(3) numbers>/<year> e.g. GEA962/16
        or RuntimeError if no reference can be generated.
        """
        year_suffix = now().strftime('%y')
        manager = self.__class__.objects

        max_retries = 10
        tries = 0
        while tries < max_retries:
            reference = '{letters}{numbers}/{year}'.format(
                letters=get_random_string(length=3, allowed_chars='ACEFHJKMNPRTUVWXY'),
                numbers=get_random_string(length=3, allowed_chars='123456789'),
                year=year_suffix
            )
            if not manager.filter(reference=reference).exists():
                return reference
            tries += 1

        # This should never happen as we have 3.5 milion choices per year
        # and it's basically unrealistic to have more than 10 collisions.
        raise RuntimeError('Cannot generate random reference')

    def save(self, *args, **kwargs):
        """
        Like the django save but it creates a reference if it doesn't exist.
        """
        if not self.reference:
            self.reference = self._calculate_reference()
        return super().save(*args, **kwargs)

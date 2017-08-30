import uuid

from django.db import models
from django.utils.crypto import get_random_string

from datahub.core.models import BaseModel

from datahub.omis.core.utils import generate_reference


class Quote(BaseModel):
    """Details of a quote."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reference = models.CharField(max_length=100)
    content = models.TextField()

    @classmethod
    def generate_reference(cls, order):
        """
        :returns: a random unused reference of form:
                <order.reference>/Q-<(2) lettes>/<(1) number> e.g. GEA962/16/Q-AB1
        :raises RuntimeError: if no reference can be generated.
        """
        def gen():
            return '{letters}{numbers}'.format(
                letters=get_random_string(length=2, allowed_chars='ACEFHJKMNPRTUVWXY'),
                numbers=get_random_string(length=1, allowed_chars='123456789')
            )
        return generate_reference(model=cls, gen=gen, prefix=f'{order.reference}/Q-')

    def __str__(self):
        """Human-readable representation"""
        return self.reference

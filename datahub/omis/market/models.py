from django.db import models

from datahub.core.models import DisableableModel
from datahub.metadata.models import Country


class Market(DisableableModel):
    """OMIS Market."""

    country = models.OneToOneField(Country, primary_key=True)
    manager_email = models.EmailField(blank=True)

    class Meta:  # noqa: D101
        verbose_name = 'OMIS Market'
        verbose_name_plural = 'OMIS Markets'

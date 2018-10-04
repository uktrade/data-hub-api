from django.contrib.postgres.fields import ArrayField
from django.db import models

from datahub.metadata.models import UKRegion


class UKRegionalSettings(models.Model):
    """OMIS settings for UK Regions."""

    uk_region = models.OneToOneField(
        UKRegion,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name='omis_settings',
    )
    manager_emails = ArrayField(
        models.EmailField(),
        blank=True,
        help_text='Comma-separated list of email addresses.',
    )

    def __str__(self):
        """Admin displayed human readable name."""
        return f'OMIS settings for {self.uk_region}'

    class Meta:
        verbose_name = 'OMIS UK regional settings'
        verbose_name_plural = 'OMIS UK regional settings'

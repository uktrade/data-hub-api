from django.db import models

from datahub.metadata.models import Country


class Market(models.Model):
    """OMIS Market."""

    country = models.OneToOneField(Country, primary_key=True)
    manager_email = models.EmailField(blank=True)
    disabled_on = models.DateTimeField(
        blank=True, null=True,
        help_text='Empty means enabled for OMIS.'
    )

    def was_disabled_on(self, date_on):
        """
        Returns True if this Country was disabled for OMIS at time `date_on`,
        False otherwise.
        """
        if not self.disabled_on:
            return False
        return self.disabled_on <= date_on

    class Meta:  # noqa: D101
        verbose_name = 'OMIS Market'
        verbose_name_plural = 'OMIS Markets'

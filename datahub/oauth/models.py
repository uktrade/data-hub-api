from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from oauth2_provider.settings import oauth2_settings


class OAuthApplicationScope(models.Model):
    """Allowed scopes for an OAuth application."""

    application = models.OneToOneField(oauth2_settings.APPLICATION_MODEL, on_delete=models.CASCADE)
    scopes = ArrayField(
        models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH),
        help_text='Allowed scopes for this application. (Comma separated in Django admin.)',
    )

    def __str__(self):
        """Human-friendly representation."""
        return str(self.application)

    class Meta:
        verbose_name = 'oauth application scope'

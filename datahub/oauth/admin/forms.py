from secrets import token_urlsafe

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy

from datahub.company.models import Advisor
from datahub.core.admin import RawIdWidget
from datahub.oauth.cache import add_token_data_to_cache


NO_SSO_EMAIL_USER_ID_MESSAGE = gettext_lazy('The adviser must have an SSO email user ID.')


class AddAccessTokenForm(forms.Form):
    """Add access token form for the admin site."""

    adviser = forms.ModelChoiceField(
        Advisor.objects.all(),
        widget=RawIdWidget(Advisor),
        label='Adviser',
        help_text='The selected adviser must have an SSO email user ID set',
    )
    expires_in_hours = forms.IntegerField(
        max_value=24 * 7,
        initial=10,
        label='Expires in (hours)',
    )

    def clean_adviser(self):
        """Validate that the adviser has an SSO email user ID."""
        adviser = self.cleaned_data['adviser']
        if not adviser.sso_email_user_id:
            raise ValidationError(NO_SSO_EMAIL_USER_ID_MESSAGE, code='no_sso_email_user_id')

        return adviser

    def save(self):
        """Add the access token to the cache."""
        token = token_urlsafe()
        adviser = self.cleaned_data['adviser']
        timeout_hours = self.cleaned_data['expires_in_hours']
        timeout = timeout_hours * 60 * 60

        add_token_data_to_cache(token, adviser.email, adviser.sso_email_user_id, timeout)
        return token, timeout_hours

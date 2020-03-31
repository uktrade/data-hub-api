from django import forms
from django.contrib.admin import widgets
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy

from datahub.company.models import Advisor
from datahub.oauth.sso_api_client import (
    get_user_by_email,
    get_user_by_email_user_id,
    SSORequestError,
    SSOUserDoesNotExist,
)

NO_MATCHING_USER_MESSAGE = gettext_lazy(
    'No matching user was found in Staff SSO. Double-check the entered details and check if the '
    'user has Data Hub access in Staff SSO.',
)
SSO_REQUEST_ERROR_MESSAGE = gettext_lazy(
    'There was an error communicating with Staff SSO: %(error)s. Please try again.',
)
DUPLICATE_USER_MESSAGE = gettext_lazy('This user has already been added to Data Hub.')

SSO_ADVISER_FIELD_MAPPING = {
    'first_name': 'first_name',
    'last_name': 'last_name',
    'sso_email_user_id': 'email_user_id',
    'email': 'email',
    'contact_email': 'contact_email',
}


class AddAdviserFromSSOForm(forms.ModelForm):
    """
    Form for adding an adviser by looking the user up in Staff SSO.

    Note: This form is designed so that it can be used as a ModelAdmin add_form.

    This is the main reason it‘s using ModelForm.
    """

    search_email = forms.EmailField(
        label='Email or SSO email user ID',
        widget=widgets.AdminEmailInputWidget,
    )

    class Meta:
        model = Advisor
        fields = ()

    def clean(self):
        """Validate the search email and fetch user details from Staff SSO."""
        data = super().clean()
        search_email = data.get('search_email')

        if not search_email:
            return data

        sso_user_data = self._get_user_data_from_sso(search_email)
        if sso_user_data:
            data['user_data'] = self._clean_sso_user_data(sso_user_data)

        return data

    def save(self, commit=True):
        """Create the adviser using looked-up information."""
        adviser = super().save(commit=False)
        user_data = self.cleaned_data['user_data']

        for field, value in user_data.items():
            setattr(adviser, field, value)

        if commit:
            adviser.save()
            # No many-to-many fields are currently set above, but this is
            # included for completeness
            self.save_m2m()

        return adviser

    def _clean_sso_user_data(self, sso_user_data):
        mapped_user_data = {
            model_field: sso_user_data[sso_field]
            for model_field, sso_field in SSO_ADVISER_FIELD_MAPPING.items()
        }
        is_duplicate = self._check_if_duplicate(mapped_user_data)

        if is_duplicate:
            return None

        return mapped_user_data

    def _get_user_data_from_sso(self, email):
        try:
            return _fetch_user_data_from_sso(email)
        except SSOUserDoesNotExist:
            error = ValidationError(NO_MATCHING_USER_MESSAGE, code='no_matching_user')
            self.add_error(None, error)
        except SSORequestError as exc:
            error = ValidationError(
                SSO_REQUEST_ERROR_MESSAGE,
                code='request_error',
                params={'error': exc},
            )
            self.add_error(None, error)

        return None

    def _check_if_duplicate(self, user_data):
        q = Q(email=user_data['email']) | Q(sso_email_user_id=user_data['sso_email_user_id'])
        is_duplicate = Advisor.objects.filter(q).exists()

        if is_duplicate:
            error = ValidationError(DUPLICATE_USER_MESSAGE, code='duplicate_user')
            self.add_error(None, error)

        return is_duplicate


def _fetch_user_data_from_sso(email):
    try:
        return get_user_by_email_user_id(email)
    except SSOUserDoesNotExist:
        return get_user_by_email(email)

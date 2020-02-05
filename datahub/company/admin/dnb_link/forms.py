from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy

from datahub.company.models import Company
from datahub.core.admin import RawIdWidget


class SelectIdsToLinkForm(forms.Form):
    """
    Form used for selecting Data Hub company id and D&B duns number for linking.
    """

    COMPANY_ALREADY_DNB_LINKED = gettext_lazy(
        'This company has already been linked with a D&B company.',
    )
    DUNS_NUMBER_ALREADY_LINKED = gettext_lazy(
        'This duns number has already been linked with a Data Hub company.',
    )

    company = forms.ModelChoiceField(
        Company.objects.all(),
        widget=RawIdWidget(Company),
        label='Data Hub Company',
    )
    duns_number = forms.CharField(min_length=9, max_length=9)

    def clean_company(self):
        """
        Check that the company does not already have a duns number.
        """
        company = self.cleaned_data['company']
        if company.duns_number:
            raise ValidationError(self.COMPANY_ALREADY_DNB_LINKED)
        return company

    def clean_duns_number(self):
        """
        Check that the duns_number chosen has not already been linked to a Data Hub company.
        """
        duns_number = self.cleaned_data['duns_number']
        if Company.objects.filter(duns_number=duns_number).exists():
            raise ValidationError(self.DUNS_NUMBER_ALREADY_LINKED)
        return duns_number

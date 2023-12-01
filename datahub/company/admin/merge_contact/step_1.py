from django import forms
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.models import Contact
from datahub.core.admin import RawIdWidget
from datahub.core.utils import reverse_with_query_string


class SelectOtherContactForm(forms.Form):
    """Form used for selecting a second contact when merging duplicate contacts"""

    BOTH_CONTACTS_ARE_THE_SAME_MSG = gettext_lazy(
        'The two contacts to merge cannot be the same. Please select a different contact.',
    )

    contact_2 = forms.ModelChoiceField(
        Contact.objects.all(),
        widget=RawIdWidget(Contact),
        label='Other contact',
    )

    def __init__(self, contact_1, *args, **kwargs):
        """Initialises the form, saving the ID of the contact already selected"""
        super().__init__(*args, **kwargs)
        self._contact_1 = contact_1

    def clean_contact_2(self):
        """Checks that a different contact than the one navigated from has been selected."""
        contact_2 = self.cleaned_data['contact_2']
        if contact_2 == self._contact_1:
            raise ValidationError(self.BOTH_CONTACTS_ARE_THE_SAME_MSG)
        return contact_2


@method_decorator(csrf_protect)
def merge_select_other_contact(model_admin, request):
    """
    First view as part of the merge duplicate contact process.

    Used to select the second contact of the two to merge.

    Note that the ID of the first contact is passed in via the query string.

    SelectOtherContactForm the form used to validate the POST body.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    contact_1 = model_admin.get_object(request, request.GET.get('contact_1'))

    if not contact_1:
        raise SuspiciousOperation()

    is_post = request.method == 'POST'
    data = request.POST if is_post else None
    form = SelectOtherContactForm(contact_1, data=data)

    if is_post and form.is_valid():
        select_primary_route_name = admin_urlname(
            model_admin.model._meta,
            'merge-select-primary-contact'
        )
        select_primary_query_args = {
            'contact_1': contact_1.pk,
            'contact_2': form.cleaned_data['contact_2'].pk,
        }
        select_primary_url = reverse_with_query_string(
            select_primary_route_name,
            select_primary_query_args,
        )
        return HttpResponseRedirect(select_primary_url)

    template_name = 'admin/company/contact/merge/step_1_select_other_contact.html'
    title = gettext_lazy('Merge with another contact')

    context = {
        **model_admin.admin_site.each_context(request),
        'opts': model_admin.model._meta,
        'title': title,
        'form': form,
        'media': model_admin.media,
        'object': contact_1,
    }
    return TemplateResponse(request, template_name, context)

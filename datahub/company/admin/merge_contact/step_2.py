import logging

from django import forms
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.merge_contact import (
    get_planned_changes,
    is_contact_a_valid_merge_source,
    is_contact_a_valid_merge_target,
    transform_merge_results_to_merge_entry_summaries,
)

from datahub.core.utils import reverse_with_query_string

logger = logging.getLogger(__name__)


class SelectPrimaryContactForm(forms.Form):
    """Form used for selecting which contact to keep as active after merging contacts."""

    INVALID_TARGET_CONTACT_MSG = gettext_lazy(
        'The contact selected is archived.',
    )
    INVALID_SOURCE_CONTACT_MSG =gettext_lazy(
        "The other contact has related records which can't be moved to the selected contact."
    )

    selected_contact = forms.ChoiceField(
        choices =(
            ('1', 'Contact 1'),
            ('2', 'Contact 2'),
        ),
        widget=forms.RadioSelect(),
    )

    def __init__(self, contact_1, contact_2, *args, **kwargs):
        """Saves a reference to the two contacts available for selection."""
        super().__init__(*args, **kwargs)

        self._contact_1 = contact_1
        self._contact_2 = contact_2
        self.invalid_objects = []

    # def clean(self):
    #     """
    #     Checks that the selection made is allowed.
    #     """
    #     cleaned_data = super().clean()
    #     contact_index = cleaned_data.get('selected_contact')

    #     if not contact_index:
    #         return

    #     target_contact = self._contact_1 if contact_index == '1' else self._contact_2
    #     source_contact = self._contact_1 if contact_index != '1' else self._contact_2

    #     if not is_contact_a_valid_merge_target(target_contact):
    #         raise ValidationError(self.INVALID_TARGET_CONTACT_MSG)

    #     is_source_valid, disallowed_objects = is_contact_a_valid_merge_source(source_contact)
    #     if not is_source_valid:
    #         error_msg = f'{self.INVALID_SOURCE_CONTACT_MSG}: Invalid object: {disallowed_objects}'
    #         logger.error(error_msg)
    #         self.invalid_objects = disallowed_objects
    #         raise ValidationError(error_msg)

    #     cleaned_data['target_contact'] = target_contact
    #     cleaned_data['source_contact'] = source_contact

    #     return cleaned_data

@method_decorator(csrf_protect)
def select_primary_contact(model_admin, request):
    """
    View for selecting the contact to retain.

    This is the view where the user selects which contact should remain as the
    active record and which one should be archived.

    Note that the IDs of the two contacts to select from are passed in via the
    query string.

    SelectPrimaryContactForm is used to validate the POST body on submission of the form.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    contact_1 = model_admin.get_object(request, request.GET.get('contact_1'))
    contact_2 = model_admin.get_object(request, request.GET.get('contact_2'))

    print(contact_1)
    print(contact_2)

    if not (contact_1 and contact_2):
        raise SuspiciousOperation()
    
    is_post = request.method == 'POST'
    data = request.POST if is_post else None
    form = SelectPrimaryContactForm(contact_1, contact_2, data=data)

    if is_post and form.is_valid():
        confirm_route_name = admin_urlname(
            model_admin.model._meta,
            'merge-confirm',
        )
        confirm_query_args = {
            'source_contact': form.cleaned_data['source_contact'].pk,
            'target_contact': form.cleaned_data['target_contact'].pk,
        }
        confirm_url = reverse_with_query_string(confirm_route_name, confirm_query_args)
        return HttpResponseRedirect(confirm_url)

    template_name = 'admin/company/contact/merge/step_2_primary_selection.html'
    title = gettext_lazy('Select which contact should be retained')

    context = {
        **model_admin.admin_site.each_context(request),
        'option_1': _build_option_context(contact_2, contact_1),
        'option_2': _build_option_context(contact_1, contact_2),
        'form': form,
        'media': model_admin.media,
        'opts': model_admin.model._meta,
        'title': title,
        'invalid_objects': form.invalid_objects,
    }

    return TemplateResponse(request, template_name, context)

def _build_option_context(source_contact, target_contact):
    merge_results, _ = get_planned_changes(target_contact)
    merge_entries = transform_merge_results_to_merge_entry_summaries(merge_results)
    is_source_valid, invalid_objects = is_contact_a_valid_merge_source(source_contact)
    is_target_valid = is_contact_a_valid_merge_target(target_contact)

    return {
        'target': target_contact,
        'merge_entries': merge_entries,
        'is_source_valid': is_source_valid,
        'is_target_valid': is_target_valid,
        'is_valid': is_source_valid and is_target_valid,
        'invalid_objects': invalid_objects,
    }

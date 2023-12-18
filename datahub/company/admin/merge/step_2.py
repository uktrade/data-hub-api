import logging

from django import forms
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.merge import (
    get_planned_changes,
    is_model_a_valid_merge_source,
    is_model_a_valid_merge_target,
    transform_merge_results_to_merge_entry_summaries,
)
from datahub.company.merge_company import (
    ALLOWED_RELATIONS_FOR_MERGING as COMPANY_ALLOWED_RELATIONS_FOR_MERGING,
    MERGE_CONFIGURATION as COMPANY_MERGE_CONFIGURATION,
)
from datahub.company.merge_contact import (
    ALLOWED_RELATIONS_FOR_MERGING as CONTACT_ALLOWED_RELATIONS_FOR_MERGING,
    MERGE_CONFIGURATION as CONTACT_MERGE_CONFIGURATION,
)
from datahub.company.models import Company, Contact
from datahub.core.utils import reverse_with_query_string


logger = logging.getLogger(__name__)


class BaseSelectPrimaryModelForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Checks that the selection made is allowed.
        """
        cleaned_data = super().clean()
        index = cleaned_data.get('selected_model')

        if not index:
            return

        target_model = self._model_1 if index == '1' else self._model_2
        source_model = self._model_1 if index != '1' else self._model_2

        if not is_model_a_valid_merge_target(target_model):
            raise ValidationError(self.INVALID_TARGET_MODEL_MSG)

        is_source_valid, disallowed_objects = is_model_a_valid_merge_source(
            source_model, self._allowed_relations_for_merging, self._model)
        if not is_source_valid:
            error_msg = f'{self.INVALID_SOURCE_MODEL_MSG}: Invalid object: {disallowed_objects}'
            logger.error(error_msg)
            self.invalid_objects = disallowed_objects
            raise ValidationError(error_msg)

        cleaned_data['target_model'] = target_model
        cleaned_data['source_model'] = source_model

        return cleaned_data


class SelectPrimaryCompanyForm(BaseSelectPrimaryModelForm):
    """Form used for selecting which company to keep as active after merging companies."""

    INVALID_TARGET_MODEL_MSG = gettext_lazy(
        'The company selected is archived.',
    )
    INVALID_SOURCE_MODEL_MSG = gettext_lazy(
        'The other company has related records which can’t be moved to the selected company.',
    )

    selected_model = forms.ChoiceField(
        choices=(
            ('1', 'Company 1'),
            ('2', 'Company 2'),
        ),
        widget=forms.RadioSelect(),
    )

    def __init__(self, company_1, company_2, *args, **kwargs):
        """Saves a reference to the two companies available for selection."""
        super().__init__(*args, **kwargs)

        self._model_1 = company_1
        self._model_2 = company_2
        self.invalid_objects = []
        self._allowed_relations_for_merging = COMPANY_ALLOWED_RELATIONS_FOR_MERGING
        self._model = Company


class SelectPrimaryContactForm(BaseSelectPrimaryModelForm):
    """Form used for selecting which contact to keep as active after merging contacts."""

    INVALID_TARGET_MODEL_MSG = gettext_lazy(
        'The contact selected is archived.',
    )
    INVALID_SOURCE_MODEL_MSG = gettext_lazy(
        "The other contact has related records which can't be moved to the selected contact.",
    )

    selected_model = forms.ChoiceField(
        choices=(
            ('1', 'Contact 1'),
            ('2', 'Contact 2'),
        ),
        widget=forms.RadioSelect(),
    )

    def __init__(self, contact_1, contact_2, *args, **kwargs):
        """Saves a reference to the two contacts available for selection."""
        super().__init__(*args, **kwargs)

        self._model_1 = contact_1
        self._model_2 = contact_2
        self.invalid_objects = []
        self._allowed_relations_for_merging = CONTACT_ALLOWED_RELATIONS_FOR_MERGING
        self._model = Contact


def select_primary_company(model_admin, request):
    template_name = 'admin/company/company/merge/step_2_primary_selection.html'
    title = gettext_lazy('Select which company should be retained')
    dict = {
        'form_class': SelectPrimaryCompanyForm,
        'template_name': template_name,
        'title': title,
        'merge_configuration': COMPANY_MERGE_CONFIGURATION,
        'allowed_relations_for_merging': COMPANY_ALLOWED_RELATIONS_FOR_MERGING,
        'model': Company,
    }
    return select_primary_model(model_admin, request, dict)


def select_primary_contact(model_admin, request):
    template_name = 'admin/company/contact/merge/step_2_primary_selection.html'
    title = gettext_lazy('Select which contact should be retained')
    dict = {
        'form_class': SelectPrimaryContactForm,
        'template_name': template_name,
        'title': title,
        'merge_configuration': CONTACT_MERGE_CONFIGURATION,
        'allowed_relations_for_merging': CONTACT_ALLOWED_RELATIONS_FOR_MERGING,
        'model': Contact,
    }
    return select_primary_model(model_admin, request, dict)


@method_decorator(csrf_protect)
def select_primary_model(model_admin, request, dict):
    """
    View for selecting the record to retain.

    This is the view where the user selects which record should remain as the
    active record and which one should be archived.

    Note that the IDs of the two records to select from are passed in via the
    query string.

    BaseSelectPrimaryModelForm is used to validate the POST body on submission of the form.
    """
    form_class = dict['form_class']

    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    model_1 = model_admin.get_object(request, request.GET.get('id_1'))
    model_2 = model_admin.get_object(request, request.GET.get('id_2'))

    if not (model_1 and model_2):
        raise SuspiciousOperation()

    is_post = request.method == 'POST'
    data = request.POST if is_post else None
    form = form_class(model_1, model_2, data=data)

    if is_post and form.is_valid():
        confirm_route_name = admin_urlname(
            model_admin.model._meta,
            'merge-confirm',
        )

        confirm_query_args = {
            'source': form.cleaned_data['source_model'].pk,
            'target': form.cleaned_data['target_model'].pk,
        }
        confirm_url = reverse_with_query_string(confirm_route_name, confirm_query_args)

        return HttpResponseRedirect(confirm_url)

    title = dict['title']
    template_name = dict['template_name']

    context = {
        **model_admin.admin_site.each_context(request),
        'option_1': _build_option_context(model_2, model_1, dict),
        'option_2': _build_option_context(model_1, model_2, dict),
        'form': form,
        'media': model_admin.media,
        'opts': model_admin.model._meta,
        'title': title,
        'invalid_objects': form.invalid_objects,
    }

    return TemplateResponse(request, template_name, context)


def _build_option_context(source, target, dict):
    merge_configuration = dict['merge_configuration']
    allowed_relations_for_merging = dict['allowed_relations_for_merging']
    model = dict['model']
    merge_results, _ = get_planned_changes(target, merge_configuration)
    merge_entries = transform_merge_results_to_merge_entry_summaries(merge_results)
    is_source_valid, invalid_objects = is_model_a_valid_merge_source(
        source, allowed_relations_for_merging, model)
    is_target_valid = is_model_a_valid_merge_target(target)

    return {
        'target': target,
        'merge_entries': merge_entries,
        'is_source_valid': is_source_valid,
        'is_target_valid': is_target_valid,
        'is_valid': is_source_valid and is_target_valid,
        'invalid_objects': invalid_objects,
    }

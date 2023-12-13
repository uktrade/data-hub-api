from django import forms
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.models import Company, Contact
from datahub.core.admin import RawIdWidget
from datahub.core.utils import reverse_with_query_string


class BaseSelectOtherModelForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_id_2(self):
        id_2 = self.cleaned_data['id_2']
        if id_2 == self._id_1:
            raise ValidationError(self.BOTH_MODELS_ARE_THE_SAME_MSG)
        return id_2


class SelectOtherCompanyForm(BaseSelectOtherModelForm):
    """Form used for selecting a second company when merging duplicate companies."""

    BOTH_MODELS_ARE_THE_SAME_MSG = gettext_lazy(
        'The two companies to merge cannot be the same. Please select a different company.',
    )

    id_2 = forms.ModelChoiceField(
        Company.objects.all(),
        widget=RawIdWidget(Company),
        label='Other company',
    )

    def __init__(self, company_1, *args, **kwargs):
        """Initialises the form, saving the ID of the company already selected."""
        super().__init__(*args, **kwargs)
        self._id_1 = company_1


class SelectOtherContactForm(BaseSelectOtherModelForm):
    """Form used for selecting a second contact when merging duplicate contacts"""

    BOTH_MODELS_ARE_THE_SAME_MSG = gettext_lazy(
        'The two contacts to merge cannot be the same. Please select a different contact.',
    )

    id_2 = forms.ModelChoiceField(
        Contact.objects.all(),
        widget=RawIdWidget(Contact),
        label='Other contact',
    )

    def __init__(self, contact_1, *args, **kwargs):
        """Initialises the form, saving the ID of the contact already selected"""
        super().__init__(*args, **kwargs)
        self._id_1 = contact_1


def merge_select_other_company(model_admin, request):
    template_name = 'admin/company/company/merge/step_1_select_other_company.html'
    title = gettext_lazy('Merge with another company')
    dict = {
        'form_class': SelectOtherCompanyForm,
        'template_name': template_name,
        'title': title,
        'next_url': 'merge-select-primary-company',
    }
    return merge_select_other_model(model_admin, request, dict)


def merge_select_other_contact(model_admin, request):
    template_name = 'admin/company/contact/merge/step_1_select_other_contact.html'
    title = gettext_lazy('Merge with another contact')
    dict = {
        'form_class': SelectOtherContactForm,
        'template_name': template_name,
        'title': title,
        'next_url': 'merge-select-primary-contact',
    }
    return merge_select_other_model(model_admin, request, dict)


@method_decorator(csrf_protect)
def merge_select_other_model(model_admin, request, dict):
    """
    First view as part of the merge duplicate records process.

    Used to select the second record of the two to merge.

    Note that the ID of the first record is passed in via the query string.

    BaseSelectOtherModelForm is used to validate the POST body.
    """
    form_class = dict['form_class']

    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    model_1 = model_admin.get_object(request, request.GET.get('id_1'))

    if not model_1:
        raise SuspiciousOperation()

    is_post = request.method == 'POST'
    data = request.POST if is_post else None
    form = form_class(model_1, data=data)

    if is_post and form.is_valid():
        select_primary_route_name = admin_urlname(
            model_admin.model._meta,
            dict['next_url'],
        )
        select_primary_query_args = {
            'id_1': model_1.pk,
            'id_2': form.cleaned_data['id_2'].pk,
        }
        select_primary_url = reverse_with_query_string(
            select_primary_route_name,
            select_primary_query_args,
        )

        return HttpResponseRedirect(select_primary_url)

    title = dict['title']
    template_name = dict['template_name']

    context = {
        **model_admin.admin_site.each_context(request),
        'opts': model_admin.model._meta,
        'title': title,
        'form': form,
        'media': model_admin.media,
        'object': model_1,
    }
    return TemplateResponse(request, template_name, context)

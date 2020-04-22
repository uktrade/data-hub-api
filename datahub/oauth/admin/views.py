from django.conf import settings
from django.contrib import admin, messages as django_messages
from django.contrib.admin import site
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.company.models import Advisor
from datahub.oauth.admin.forms import AddAccessTokenForm

SUCCESS_MESSAGE_TEMPLATE = gettext_lazy(
    'Access token <code style="user-select: all">{token}</code> added and will expire in '
    '{timeout_hours} hours.',
)


@csrf_protect
def add_access_token_view(request):
    """
    View for adding an an access token.

    Requires superuser access.
    """
    if not settings.ENABLE_ADMIN_ADD_ACCESS_TOKEN_VIEW:
        raise Http404()

    if not request.user.is_superuser:
        raise PermissionDenied()

    is_post = request.method == 'POST'
    initial = {'adviser': request.user}
    data = request.POST if is_post else None
    form = AddAccessTokenForm(initial=initial, data=data)

    if is_post and form.is_valid():
        token, timeout_hours = form.save()

        message = format_html(SUCCESS_MESSAGE_TEMPLATE, token=token, timeout_hours=timeout_hours)
        django_messages.add_message(request, django_messages.SUCCESS, message)
        admin_index = reverse('admin:index')
        return HttpResponseRedirect(admin_index)

    template_name = 'admin/oauth/add_access_token.html'
    # The only way to get the standard list of media files is via a ModelAdmin,
    # so, unfortunately, we have to create one here to get needed .js files loaded
    model_admin = admin.ModelAdmin(Advisor, site)
    context = {
        'form': form,
        'media': model_admin.media,
        'title': gettext('Add access token'),
    }
    return TemplateResponse(request, template_name, context)

from functools import partial

from django.http import HttpResponse
from django.views.decorators.http import require_POST

from company.models import Company, Contact, Interaction

EXPOSED_MODELS = (Company, Contact, Interaction)


@require_POST
def korben_view(model, request):
    """View for Korben."""
    data = request.POST
    model.object.update_or_create(defaults=data, id=data['id'])
    return HttpResponse('OK')


urls_args = []

for model in EXPOSED_MODELS:
    name = model._meta.db_table
    fn = partial(korben_view, model)
    path = r'{0}/$'.format(name)
    urls_args.append(((path, fn), {'name': name}))

from functools import partial

from django.http import HttpResponse
from django.views.decorators.http import require_POST

from company.models import Company, Contact, Interaction

EXPOSED_MODELS = (Company, Contact, Interaction)


@require_POST
def korben_view(request, model):
    """View for Korben."""

    data = request.POST.dict()
    try:
        obj = model.objects.get(id=data['id'])
        for key, value in data.items():
            setattr(obj, key, value)
    except model.DoesNotExist:
        obj = model(**data)
    obj.save(use_korben=False)  # data come from Korben, don't need to double check

    return HttpResponse('OK')


urls_args = []

for model in EXPOSED_MODELS:
    name = model._meta.db_table
    fn = partial(korben_view, model=model)
    path = r'{0}/$'.format(name)
    urls_args.append(((path, fn), {'name': name}))

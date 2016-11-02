from functools import partial

from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes

from company.models import Advisor, Company, Contact, Interaction
from .authentication import KorbenSharedSecretAuthentication
EXPOSED_MODELS = (Advisor, Company, Contact, Interaction)


@api_view(['POST'])
@authentication_classes((KorbenSharedSecretAuthentication, ))
def korben_view(request, model):
    """View for Korben."""

    data = request.POST.dict()
    try:
        obj = model.objects.get(id=data['id'])
        for key, value in data.items():
            setattr(obj, key, value)
    except model.DoesNotExist:
        obj = model(**data)
    obj.save(as_korben=True)  # data come from Korben, kill validation

    return HttpResponse('OK')


urls_args = []

for model in EXPOSED_MODELS:
    name = model._meta.db_table
    fn = partial(korben_view, model=model)
    path = r'{0}/$'.format(name)
    urls_args.append(((path, fn), {'name': name}))


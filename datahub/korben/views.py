from functools import partial

from dateutil.parser import parse as parse_date
from django.db.models.fields import DateTimeField
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from datahub.company.models import Advisor, Company, Contact, Interaction
from .authentication import KorbenSharedSecretAuthentication

EXPOSED_MODELS = (Advisor, Company, Contact, Interaction)


@api_view(['POST'])
@authentication_classes((KorbenSharedSecretAuthentication, ))
def korben_view(request, model):
    """View for Korben."""

    data = request.data
    try:
        obj = model.objects.get(pk=data['id'])
        for key, value in data.items():
            setattr(obj, key, value)
    except model.DoesNotExist:
        obj = model(**data)

    # create datetime objects for datetime fields
    for field in obj._meta.fields:
        if isinstance(field, DateTimeField):
            try:
                date_obj = parse_date(getattr(obj, field.name, None))
                setattr(obj, field.name, date_obj)
            except (ValueError, AttributeError):
                if field.null:
                    pass
                else:
                    return Response(data=data, status=HTTP_400_BAD_REQUEST)

    obj.save(as_korben=True)  # data comes from Korben, kill validation

    return Response(data={'message': 'OK'})


urls_args = []

for model in EXPOSED_MODELS:
    name = model._meta.db_table
    fn = partial(korben_view, model=model)
    path = r'{0}/$'.format(name)
    urls_args.append(((path, csrf_exempt(fn)), {'name': name}))

'''
Functions for transforming dicts from Django to OData shape and back again,
according to spec.MAPPINGS
'''
import datetime
import functools
from logging import getLogger

from django.db.models.fields import DateTimeField

from datahub.core import constants
from datahub.korben.utils import cdms_datetime_to_datetime

from . import spec
from . import utils

logger = getLogger(__name__)

def extract(bucket, entity_name):
    """Extract data from bucket using given prefix and mapping spec."""
    return utils.iterate_over_cdms_entities_from_s3(bucket, entity_name)


def transform(mapping, odata_dict):
    'Transform an OData dict to a Django dict'
    django_dict = {mapping.ToModel._meta.pk.name: odata_dict[mapping.pk]}

    for left, right in mapping.fields:

        value = utils.get_by_path(odata_dict, left)

        # set undefined if required
        if value is None and mapping[left] in mapping.undef:
            value = constants.Undefined

        # transform to compatible datetime string
        if isinstance(mapping.ToModel._meta.get_field(right), DateTimeField):
            value = utils.cdms_datetime_to_datetime(value)

        django_dict[right] = value

    # concat as required
    for lefts, right in mapping.concat:
        value = functools.reduce(
            lambda acc, left: acc + (odata_dict.get(left) or ''), lefts, ''
        )
        django_dict[right] = value

    return django_dict


def load(Model, data):
    try:
        obj_id = data.pop('id')
        obj, created = Model.objects.get_or_create(id=obj_id, defaults=data)
        if not created:
            for name, value in data.items():
                setattr(obj, name, value)
            obj.save()

    except Exception as e:
        print(e)
        logger.exception('Exception during importing data')

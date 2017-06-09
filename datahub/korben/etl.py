"""
ETL.

Extract, transform and load functions for converting from CDMS JSON to Postgres
rows via Django models according to specs.mappings.
"""
import functools
from logging import getLogger

from django.db.models.fields import DateTimeField

from . import utils

logger = getLogger(__name__)


def extract(bucket, entity_name):
    """Extract data from bucket using given prefix and mapping spec."""
    return utils.iterate_over_cdms_entities_from_s3(bucket, entity_name)


def transform(mapping, odata_dict):
    """Transform an OData dict to a Django dict."""
    django_dict = {mapping.ToModel._meta.pk.name: odata_dict[mapping.pk]}

    for left, right in mapping.fields:

        value = utils.get_by_path(odata_dict, left)
        django_dict[right] = value

        # transform to compatible datetime string
        if isinstance(mapping.ToModel._meta.get_field(right), DateTimeField):
            django_dict[right] = utils.cdms_datetime_to_datetime(value)

    # concat as required
    for lefts, right, sep in mapping.concat:
        values = (odata_dict.get(left) or '' for left in lefts)
        django_dict[right] = sep.join(values)

    return django_dict


def load(Model, data):  # noqa N803
    """Get or create and save Model instance from data."""
    try:
        obj_id = data.pop('id')
        obj, created = Model.objects.get_or_create(id=obj_id, defaults=data)
        if not created:
            for name, value in data.items():
                setattr(obj, name, value)
            obj.save()

    except Exception as e:
        logger.exception(e)
        logger.exception('Exception during importing data')

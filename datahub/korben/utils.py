import collections
import datetime
import io
import json
import re
import tempfile

from logging import getLogger

from django.db.models.fields.related import ForeignKey

from . import spec

logger = getLogger(__name__)
DATETIME_RE = re.compile(r'/Date\(([-+]?\d+)\)/')
PREFIX = 'CACHE/XRMServices/2011/OrganizationData.svc/'


def yield_fkeys(Model):  # noqa N803
    """Return mapped foreignkeys for a model."""
    mapping = spec.get_mapping(Model)
    for field in Model._meta.get_fields():
        if isinstance(field, ForeignKey) and field.column in mapping:
            if len(field.foreign_related_fields) > 1:
                raise Exception('Composite foreign keys are not supported')
            yield field.foreign_related_fields[0].model


def fkey_deps(models):
    """Return dict showing dependencies of model set."""
    if not isinstance(models, set):
        raise Exception('Pass a set of models')
    dependencies = collections.defaultdict(set)
    added = set()
    depth = 0
    # run until we've covered all models
    while len(added) < len(models):
        remaining = filter(lambda x: x not in added, models)
        for Model in remaining:
            model_deps = set(yield_fkeys(Model))
            if model_deps.difference(models):
                model_dep = model_deps.pop()
                msg = (f'{model_dep} is a dependency of {Model} but is not '
                       f'being passed')
                raise Exception(msg)
            # if deps are all added to previous (less deep) depths, we are deep
            # enough to add this model; do so
            lesser_deps = set()
            for lesser_depth in range(0, depth):
                lesser_deps = lesser_deps.union(dependencies[lesser_depth])
            if model_deps.issubset(lesser_deps):
                dependencies[depth].add(Model)
                added.add(Model)
        depth += 1
        # bail if it gets too heavy
        if depth > 10:
            raise Exception('fkey deps are too deep')
    return dependencies


def cdms_datetime_to_datetime(value):
    """Parses a cdms datetime as string and returns the equivalent datetime value. Dates in CDMS are always UTC."""
    if not value:
        return None

    if isinstance(value, datetime.datetime):
        return value

    match = DATETIME_RE.match(value or '')
    if match:
        parsed_val = int(match.group(1))
        parsed_val = datetime.datetime.utcfromtimestamp(parsed_val / 1000)
        return parsed_val.replace(tzinfo=datetime.timezone.utc)
    else:
        logger.warning('Unrecognized value for a datetime: %s returning '
                       '`None` instead', value)
        return None


def load_json_from_s3_bucket(bucket, key):  # noqa
    """Download and read a JSON file form S3 bucket."""
    with tempfile.TemporaryFile() as f:
        bucket.download_fileobj(key, f)
        f.seek(0, 0)
        return json.load(io.TextIOWrapper(f))


def iterate_over_cdms_entities_from_s3(bucket, entity_name):
    """Combine all entities from multiple cdms dump pages into single stream of JSON objects."""
    for key in get_cdms_entity_s3_keys(bucket, entity_name):
        print(f'Processing: {key}')  # noqa: T003
        json_data = load_json_from_s3_bucket(bucket, key)
        try:
            results = json_data['d']['results']
        except KeyError:
            logger.error('Failed to load result page: %s', key)
            results = []

        for row in results:
            yield row


def get_cdms_entity_s3_keys(bucket, entity_name):
    """Filter the relevant S3 keys for CDMS entity."""
    all_objects = bucket.objects.filter(Prefix=PREFIX + entity_name)
    for k in all_objects:
        if k.key.endswith('response_body'):
            yield k.key


def get_by_path(srcdict, path):
    """Get a value for a dict by dotted path."""
    value = srcdict
    for chunk in path.split('.'):
        value = value.get(chunk)
    return value

import datetime
import io
import json
import re
import tempfile
from logging import getLogger

logger = getLogger(__name__)
DATETIME_RE = re.compile(r'/Date\(([-+]?\d+)\)/')
PREFIX = 'CACHE/XRMServices/2011/OrganizationData.svc/'


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
        logger.warning('Unrecognized value for a datetime: {} returning `None` instead'.format(value))
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
        print('Processing: {}'.format(key))  # noqa: T003
        json_data = load_json_from_s3_bucket(bucket, key)
        try:
            results = json_data['d']['results']
        except KeyError:
            logger.error('Failed to load result page: {}'.format(key))
            results = []

        for row in results:
            yield row


def get_cdms_entity_s3_keys(bucket, entity_name):
    """Filter the relevant S3 keys for CDMS entity."""
    all_objects = bucket.objects.filter(Prefix=PREFIX + entity_name)
    filtered_objects = []
    for k in all_objects:
        if k.key.endswith('response_body'):
            yield k.key

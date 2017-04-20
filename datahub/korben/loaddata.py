import functools
import os
from collections import namedtuple, OrderedDict
from logging import getLogger

import boto3

from . import etl


logger = getLogger(__name__)


s3 = boto3.resource(
    's3',
    region_name='eu-west-2',
    aws_access_key_id=os.environ['CDMS_DUMP_S3_KEY_ID'],
    aws_secret_access_key=os.environ['CDMS_DUMP_S3_KEY'],
)
s3_bucket = s3.Bucket(os.environ['CDMS_DUMP_S3_BUCKET'])

local_apps = ('company', 'interaction', 'metadata')
models = itertools.chain.from_iterable(
    apps.get_app_config(name).models.values() for name in local_apps
)
model_deps = dict(
    utils.fkey_deps(
        set(filter(lambda M: not M._meta.auto_created, models))
    )
)

for depth in model_deps.keys():
    for Model in model_deps[depth]:
        mapping = spec.get_mapping(Model)
        data_raw = extract(s3_bucket, mapping.from_entitytype)
        data_transformed = map(functools.partial(etl.transform, mapping), data)
        for item in data_transformed:
            load(mapping.ToModel, item)

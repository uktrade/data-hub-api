import functools
from .. import config
from .. import services
from . import spec, extract, transform, load


def from_cdms_psql(entity_name, guids, idempotent=False):
    cdms_tablename = entity_name + 'Set'
    mapping = spec.MAPPINGS[cdms_tablename]
    metadata = services.db.poll_for_metadata(config.database_odata_url)
    result = extract.from_cdms_psql(metadata, cdms_tablename, guids)
    transform_func = functools.partial(
        transform.from_cdms_psql, cdms_tablename
    )
    if not idempotent:
        return load.to_leeloo(mapping['to'], map(transform_func, result))
    return load.to_leeloo_idempotent(
        mapping['to'], map(transform_func, result)
    )

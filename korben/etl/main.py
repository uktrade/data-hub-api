import functools
from korben import config, services
from . import spec, extract, transform, load


def from_cdms_psql(table, guids, idempotent=True):
    mapping = spec.MAPPINGS[table.name]
    result = extract.from_cdms_psql(table, guids)
    transform_func = functools.partial(transform.from_cdms_psql, table)
    django_metadata = services.db.poll_for_metadata(config.database_url)
    django_table = django_metadata.tables[mapping['to']]
    if not idempotent:
        return load.to_leeloo(django_table, map(transform_func, result))
    return load.to_leeloo_idempotent(django_table, map(transform_func, result))

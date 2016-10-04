import functools

from korben import config, services, etl
from korben.sync import utils as sync_utils

from . import spec, extract, transform, load


def from_odata_json(table, json_path):
    entries = sync_utils.parse_json_entries(None, None, None, json_path)
    col_names = [col.name for col in table.columns]
    rows = map(
        functools.partial(sync_utils.entry_row, col_names, None), entries
    )
    return etl.load.to_sqla_table_idempotent(table, rows)


def from_cdms_psql(table, guids, idempotent=True):
    mapping = spec.MAPPINGS[table.name]
    result = extract.from_cdms_psql(table, guids)
    transform_func = functools.partial(transform.from_cdms_psql, table)
    django_metadata = services.db.poll_for_metadata(config.database_url)
    django_table = django_metadata.tables[mapping['to']]

    # TODO: call the leeloo API instead of database directly
    if idempotent:
        load_func = load.to_sqla_table_idempotent
    else:
        load_func = load.to_sqla_table

    return load_func(django_table, map(transform_func, result))

import functools

from korben import services, etl, utils

from . import spec, extract, transform, load


def from_odata_json(table, json_path):
    entries = utils.parse_json_entries(None, None, None, json_path)
    col_names = [col.name for col in table.columns]
    rows = map(functools.partial(utils.entry_row, col_names), entries)
    return etl.load.to_sqla_table_idempotent(table, rows)


def from_odata(table, guids, idempotent=True):
    mapping = spec.MAPPINGS[table.name]
    result = extract.from_odata(table, guids)
    transform_func = functools.partial(transform.odata_to_django, table.name)
    django_metadata = services.db.get_django_metadata()
    django_table = django_metadata.tables[mapping['to']]

    # TODO: call the leeloo API instead of database directly
    if idempotent:
        load_func = load.to_sqla_table_idempotent
    else:
        load_func = load.to_sqla_table

    return load_func(django_table, map(transform_func, result))

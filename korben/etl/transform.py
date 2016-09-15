import sqlalchemy as sqla
from . import spec


def from_cdms_psql(table, cdms_dict):
    'Transform a CDMS row into a row suitable for insertion in to Leeloo'
    out_dict = {}
    mapping = spec.MAPPINGS[table.name]
    for cdms_col, leeloo_col in mapping.get('local', []):
        if cdms_col:  # TODO: Should these even appear in mappings?
            out_dict[leeloo_col] = cdms_dict[cdms_col]
    for cdms_cols, leeloo_col, func in mapping.get('local_fn', []):
        args = []
        for cdms_col in cdms_cols:
            args.append(cdms_dict[cdms_col])
        out_dict[leeloo_col] = func(*args)
    for fkey, leeloo_col in mapping.get('foreign', []):
        join_col, remote_tablename, remote_col = fkey
        remote_table = table.metadata.tables[remote_tablename]
        primary_key = next(
            col.name for col in remote_table.primary_key.columns.values()
        )
        select_statement = (
            sqla
            .select([remote_table.c[remote_col]])
            .where(remote_table.columns[primary_key] == cdms_dict[join_col])
        )
        value = table.metadata.bind.execute(select_statement).scalar()
        out_dict[leeloo_col] = value
    return out_dict

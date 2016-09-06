import sqlalchemy as sqla
from . import spec


def to_leeloo(metadata, cdms_tablename, entry_dict):
    'Transform a CDMS entry into a row suitable for insertion in to Leeloo'
    out_dict = {}
    mapping = spec.MAPPINGS[cdms_tablename]
    for cdms_col, leeloo_col in mapping['local']:
        out_dict[leeloo_col] = entry_dict[cdms_col]
    for (cdms_tablename, cdms_col), leeloo_col in mapping['foreign']:
        table = metadata.tables[cdms_tablename]
        primary_key = next(
            col.name for col in table.primary_key.columns.values()
        )
        select_statement = (
            sqla
            .select([table.c[cdms_col]], table)
            .where(table.columns[primary_key] == out_dict['id'])
        )
        value = metadata.bind.connect()\
                             .execute(select_statement)\
                             .fetchone()\
                             .scalar()
        out_dict[leeloo_col] = value
    return out_dict

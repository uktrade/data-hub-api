import sqlalchemy as sqla
from korben import config
from .. import services
from . import spec


def from_cdms_psql(cdms_tablename, cdms_dict):
    'Transform a CDMS row into a row suitable for insertion in to Leeloo'
    metadata = services.db.poll_for_metadata(config.database_odata_url)
    out_dict = {}
    mapping = spec.MAPPINGS[cdms_tablename]
    for cdms_col, leeloo_col in mapping.get('local', []):
        if cdms_col:  # TODO: Should these even appear in mappings?
            out_dict[leeloo_col] = cdms_dict[cdms_col]
    for fkey, leeloo_col in mapping.get('foreign', []):
        join_col, remote_tablename, remote_col = fkey
        remote_table = metadata.tables[remote_tablename]
        primary_key = next(
            col.name for col in remote_table.primary_key.columns.values()
        )
        select_statement = (
            sqla
            .select([remote_table.c[remote_col]])
            .where(remote_table.columns[primary_key] == cdms_dict[join_col])
        )
        value = metadata.bind.execute(select_statement).scalar()
        out_dict[leeloo_col] = value
    return out_dict

import sqlalchemy as sqla

def from_cdms_psql(metadata, entity_name, guids):
    table = metadata.tables[entity_name]
    primary_key = next(
        col.name for col in table.primary_key.columns.values()
    )
    select_statement = (
        sqla
        .select([table])
        .where(table.columns[primary_key].in_(guids))
    )
    result = metadata.bind.connect().execute(select_statement).fetchall()
    return map(dict, result)

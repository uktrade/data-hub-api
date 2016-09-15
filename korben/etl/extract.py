import sqlalchemy as sqla


def from_cdms_psql(table, guids):
    primary_key = next(
        col.name for col in table.primary_key.columns.values()
    )
    select_statement = (
        sqla
        .select([table])
        .where(table.columns[primary_key].in_(guids))
    )
    result = table.metadata.bind.connect().execute(select_statement).fetchall()
    return map(dict, result)


def from_django_psql(metadata, django_tablename, pks):
    pass
